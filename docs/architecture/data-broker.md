## Data Broker

### Overview

The Data Broker is a core component of the backend that manages external data retrieval, caching, and formatting. It acts as an intermediary between policy execution and external data sources, providing intelligent caching, request management, and response transformation.

**Location**: `vulkan-engine/vulkan_engine/data/broker.py`

### Architecture

The Data Broker consists of three main components:

1. **DataBroker** - Main orchestrator for data requests
2. **CacheManager** - Handles cache lookup, storage, and TTL management
3. **Request Builder** - Constructs HTTP requests from data source specs (via `vulkan.connections`)

### Core Responsibilities

- **Data Retrieval**: Fetch data from external HTTP sources
- **Intelligent Caching**: Cache responses with configurable TTL to reduce external calls
- **Response Formatting**: Transform responses (JSON, XML, CSV, plain text) into usable formats
- **Request Tracking**: Record all data requests for analytics and debugging
- **Error Handling**: Gracefully handle network failures and malformed responses

---

## Data Flow

### 1. Request Initiation

A policy run triggers a data request through the `DataSourceService`:

```python
# vulkan_engine/services/data_source.py
def request_data_from_broker(
    self, request: DataBrokerRequest, project_id: str = None
) -> DataBrokerResponse:
```

**Request Parameters**:
- `data_source_name`: Name of the configured data source
- `configured_params`: Runtime parameters for the request (e.g., query params, body)
- `run_id`: Associated policy run ID for tracking

### 2. Data Source Resolution

The service resolves the data source by name and loads its specification:

```python
data_source = self.data_source_loader.get_data_source_by_name(
    name=request.data_source_name, 
    project_id=project_id, 
    include_archived=True
)
spec = DataSourceSchema.from_orm(data_source)
```

**Data Source Spec** includes:
- HTTP configuration (URL, method, headers, params, body)
- Caching settings (enabled, TTL)
- Response type (JSON, XML, CSV, PLAIN_TEXT)
- Environment variables (credentials, tokens)
- Runtime parameters (templated fields)

### 3. Environment Variable Injection

Environment variables (secrets, tokens) are loaded from the database:

```python
env_vars = self.db.query(DataSourceEnvVar).filter_by(
    data_source_id=spec.data_source_id
).all()
env_variables = {ev.name: ev.value for ev in env_vars}
```

Missing required variables trigger an `InvalidDataSourceException`.

### 4. Cache Lookup

The broker generates a cache key from the data source ID and configured parameters:

```python
def make_cache_key(spec: schemas.DataSource, variables: dict) -> str:
    content = dict(data_source_id=str(spec.data_source_id), variables=variables)
    content_str = json.dumps(content, sort_keys=True)
    return hashlib.md5(content_str.encode("utf-8")).hexdigest()
```

If caching is enabled, the `CacheManager` checks for a valid cached entry:

```python
if self.spec.caching.enabled:
    data = cache.get_data(key)
    if data is not None:
        return schemas.DataBrokerResponse(
            data_object_id=data.data_object_id,
            origin=schemas.DataObjectOrigin.CACHE,
            key=key,
            value=self._format_data(data.value),
            start_time=None,
            end_time=None,
            error=None,
        )
```

**Cache Hit**: Returns immediately with `origin=CACHE`  
**Cache Miss or Expired**: Proceeds to external request

### 5. HTTP Request Construction

The broker uses `vulkan.connections.make_request` to build a prepared HTTP request:

```python
req = make_request(self.spec.source, configured_params, env_variables)
```

**Template Resolution**:
- URL, headers, params, and body support templating with `{{ variable }}`
- Variables are resolved from `configured_params` (runtime) and `env_variables` (secrets)

**Example**:
```json
{
  "url": "https://api.example.com/users/{{ user_id }}",
  "method": "GET",
  "headers": {
    "Authorization": "Bearer {{ api_token }}"
  },
  "params": {
    "include": "profile"
  }
}
```

Resolves to:
```
GET https://api.example.com/users/12345?include=profile
Authorization: Bearer abc123token
```

### 6. External Request Execution

The broker sends the request with retry logic and timeout:

```python
response = requests.Session().send(req, timeout=self.spec.source.timeout)
response.raise_for_status()
```

**Timing**: Start and end times are captured for performance tracking.

### 7. Response Storage

On success (200 OK), the raw response is stored as a `DataObject`:

```python
data = DataObject(
    key=key,
    value=response.content,  # Raw bytes
    data_source_id=self.spec.data_source_id,
)
self.db.add(data)
self.db.commit()
```

**DataObject Table**:
- `data_object_id`: UUID primary key
- `data_source_id`: Foreign key to data source
- `key`: Cache key (MD5 hash)
- `value`: Raw response bytes
- `created_at`: Timestamp

### 8. Cache Update

If caching is enabled, the cache entry is created:

```python
if self.spec.caching.enabled:
    cache.set_cache(key, data.data_object_id)
```

**RunDataCache Table**:
- `key`: Cache key (primary key)
- `data_object_id`: Foreign key to data object
- `created_at`: Timestamp for TTL calculation

### 9. Response Formatting

The broker formats the response based on the configured `response_type`:

```python
def _format_data(self, value: bytes):
    data = value.decode("utf-8")
    response_type = self.spec.source.response_type
    
    if response_type == ResponseType.JSON.value:
        return json.loads(data)
    elif response_type == ResponseType.XML.value:
        return _xml_to_dict(ET.fromstring(data))
    elif response_type == ResponseType.CSV.value:
        csv_reader = csv.DictReader(io.StringIO(data))
        return list(csv_reader)
    return data  # PLAIN_TEXT
```

**Supported Formats**:
- **JSON**: Parsed into dict/list
- **XML**: Converted to nested dict structure
- **CSV**: Parsed into list of dicts (one per row)
- **PLAIN_TEXT**: Returned as string

### 10. Request Tracking

Every broker request is recorded in `RunDataRequest` for analytics:

```python
request_obj = RunDataRequest(
    run_id=request.run_id,
    data_object_id=data.data_object_id,
    data_source_id=spec.data_source_id,
    data_origin=data.origin,  # CACHE or REQUEST
    start_time=data.start_time,
    end_time=data.end_time,
    error=data.error,
)
self.db.add(request_obj)
self.db.commit()
```

**Tracked Metrics**:
- Which data source was used
- Cache hit vs. miss
- Request latency (start_time, end_time)
- Errors (if any)

---

## Database Schema

### DataSource
Stores data source configurations.

| Column | Type | Description |
|--------|------|-------------|
| `data_source_id` | UUID | Primary key |
| `name` | String | Unique name |
| `description` | String | Optional description |
| `source` | JSON | HTTP config (url, method, headers, etc.) |
| `caching_enabled` | Boolean | Enable caching |
| `caching_ttl` | Integer | TTL in seconds (null = infinite) |
| `runtime_params` | Array[String] | Templated param names |
| `variables` | Array[String] | Required env var names |
| `status` | Enum | DRAFT, PUBLISHED, ARCHIVED |
| `project_id` | UUID | Multi-tenant isolation |

### DataSourceEnvVar
Stores environment variables (secrets, tokens) for data sources.

| Column | Type | Description |
|--------|------|-------------|
| `data_source_env_var_id` | UUID | Primary key |
| `data_source_id` | UUID | Foreign key |
| `name` | String | Variable name |
| `value` | JSON | Variable value (encrypted at rest recommended) |
| `nullable` | Boolean | Allow null values |

### DataObject
Immutable storage for fetched data.

| Column | Type | Description |
|--------|------|-------------|
| `data_object_id` | UUID | Primary key |
| `data_source_id` | UUID | Foreign key |
| `key` | String | Cache key (MD5 hash) |
| `value` | LargeBinary | Raw response bytes |
| `created_at` | Timestamp | Creation time |

### RunDataCache
Cache index mapping keys to data objects.

| Column | Type | Description |
|--------|------|-------------|
| `key` | String | Cache key (primary key) |
| `data_object_id` | UUID | Foreign key to DataObject |
| `created_at` | Timestamp | For TTL calculation |

### RunDataRequest
Audit log of all data requests.

| Column | Type | Description |
|--------|------|-------------|
| `run_data_request_id` | UUID | Primary key |
| `run_id` | UUID | Foreign key to Run |
| `data_object_id` | UUID | Foreign key to DataObject |
| `data_source_id` | UUID | Foreign key to DataSource |
| `data_origin` | Enum | CACHE or REQUEST |
| `start_time` | Float | Request start (epoch) |
| `end_time` | Float | Request end (epoch) |
| `error` | JSON | Error details (if any) |
| `created_at` | Timestamp | Record creation time |

---

## Caching Strategy

### TTL Management

The `CacheManager` checks TTL on every cache lookup:

```python
def get_data(self, key: str) -> DataObject | None:
    cache = self.db.query(RunDataCache).filter_by(key=key).first()
    if cache is None:
        return None
    
    data = self.db.query(DataObject).filter_by(
        data_object_id=cache.data_object_id
    ).first()
    
    ttl = self.spec.caching.ttl
    elapsed = (datetime.now(timezone.utc) - data.created_at).total_seconds()
    
    if ttl is not None and elapsed > ttl:
        self.db.delete(cache)
        self.db.commit()
        return None  # Cache expired
    
    return data
```

**TTL Behavior**:
- `ttl=None`: Cache never expires
- `ttl=N`: Cache expires after N seconds
- Expired entries are deleted on next lookup

### Cache Key Design

Cache keys are deterministic hashes of:
1. Data source ID
2. Configured parameters (sorted JSON)

**Example**:
```python
{
  "data_source_id": "550e8400-e29b-41d4-a716-446655440000",
  "variables": {"user_id": "12345", "include": "profile"}
}
# MD5: "a3f2b1c9d8e7f6a5b4c3d2e1f0a9b8c7"
```

This ensures:
- Same params = same cache key
- Different params = different cache key
- Cache invalidation on data source changes (new ID)

---

## Error Handling

### Exception Hierarchy

```
VulkanServerException
├── DataSourceNotFoundException (404)
├── InvalidDataSourceException (400)
├── DataBrokerRequestException (502)
└── DataBrokerException (500)
```

### Error Scenarios

1. **Data Source Not Found** (404)
   - Data source name doesn't exist
   - Raised by: `DataSourceService.request_data_from_broker`

2. **Missing Environment Variables** (400)
   - Required env vars not configured
   - Raised before broker initialization

3. **Network/HTTP Errors** (502)
   - Connection timeout
   - DNS resolution failure
   - HTTP 4xx/5xx responses
   - Wrapped as `DataBrokerRequestException`

4. **Internal Errors** (500)
   - Parsing failures
   - Database errors
   - Wrapped as `DataBrokerException`

### Error Response Format

Errors are captured in the `DataBrokerResponse`:

```python
DataBrokerResponse(
    data_object_id=None,
    origin=None,
    key=None,
    value=None,
    start_time=start_time,
    end_time=end_time,
    error={"message": "Connection timeout", "code": "TIMEOUT"}
)
```

---

## API Endpoints

### Internal Data Broker Endpoint

**POST** `/internal/data-broker`

Used by orchestrators (Dagster/Hatchet) during policy execution.

**Request**:
```json
{
  "data_source_name": "user_api",
  "configured_params": {
    "user_id": "12345"
  },
  "run_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**:
```json
{
  "data_object_id": "660f9511-f39c-52e5-b827-557766551111",
  "origin": "REQUEST",
  "key": "a3f2b1c9d8e7f6a5b4c3d2e1f0a9b8c7",
  "value": {
    "id": "12345",
    "name": "John Doe",
    "email": "john@example.com"
  },
  "start_time": 1699564800.123,
  "end_time": 1699564800.456,
  "error": null
}
```

**Handler**: `vulkan_server/routers/internal.py`

---

## Usage in Policy Execution

### Data Input Node

Policies use **Data Input Nodes** to fetch data via the broker:

```python
# vulkan/vulkan/runners/beam/nodes.py
class BeamDataInput(DataInputNode, BeamNode):
    def expand(self, pcoll):
        # Calls broker via app client
        response = self.app_client.request_data_from_broker(
            data_source_name=self.config.data_source_name,
            configured_params=self.config.params,
            run_id=self.run_id
        )
        return pcoll | beam.Create([response.value])
```

### Workflow Integration

1. Policy defines data dependencies
2. Orchestrator schedules data input nodes
3. Nodes call broker via internal API
4. Broker returns formatted data
5. Data flows through policy graph

---

## Monitoring & Analytics

### Key Metrics

Track via `RunDataRequest` table:

- **Cache Hit Rate**: `COUNT(*) WHERE data_origin='CACHE' / COUNT(*)`
- **Average Latency**: `AVG(end_time - start_time) WHERE data_origin='REQUEST'`
- **Error Rate**: `COUNT(*) WHERE error IS NOT NULL / COUNT(*)`
- **Top Data Sources**: `COUNT(*) GROUP BY data_source_id`

### Query Example

```sql
SELECT 
  ds.name,
  COUNT(*) as total_requests,
  SUM(CASE WHEN rdr.data_origin = 'CACHE' THEN 1 ELSE 0 END) as cache_hits,
  AVG(rdr.end_time - rdr.start_time) as avg_latency_sec
FROM run_data_request rdr
JOIN data_source ds ON rdr.data_source_id = ds.data_source_id
WHERE rdr.created_at > NOW() - INTERVAL '1 day'
GROUP BY ds.name
ORDER BY total_requests DESC;
```

---

## Configuration Examples

### Example 1: REST API with Auth

```json
{
  "name": "github_user_api",
  "source": {
    "url": "https://api.github.com/users/{{ username }}",
    "method": "GET",
    "headers": {
      "Authorization": "token {{ github_token }}",
      "Accept": "application/vnd.github.v3+json"
    },
    "response_type": "JSON",
    "timeout": 30
  },
  "caching": {
    "enabled": true,
    "ttl": 3600
  },
  "runtime_params": ["username"],
  "variables": ["github_token"]
}
```

### Example 2: CSV Data Source

```json
{
  "name": "product_catalog",
  "source": {
    "url": "https://data.company.com/products.csv",
    "method": "GET",
    "response_type": "CSV",
    "timeout": 60
  },
  "caching": {
    "enabled": true,
    "ttl": 86400
  },
  "runtime_params": [],
  "variables": []
}
```

### Example 3: SOAP/XML API

```json
{
  "name": "legacy_soap_api",
  "source": {
    "url": "https://legacy.system.com/soap",
    "method": "POST",
    "headers": {
      "Content-Type": "text/xml",
      "SOAPAction": "GetCustomer"
    },
    "body": {
      "xml": "<soap:Envelope>...</soap:Envelope>"
    },
    "response_type": "XML",
    "timeout": 45
  },
  "caching": {
    "enabled": false
  }
}
```

---

## Code References

- **Broker**: `vulkan-engine/vulkan_engine/data/broker.py`
- **Service**: `vulkan-engine/vulkan_engine/services/data_source.py`
- **DB Models**: `vulkan-engine/vulkan_engine/db.py`
- **HTTP Config**: `vulkan/vulkan/connections.py`
- **API Router**: `vulkan-server/vulkan_server/routers/internal.py`


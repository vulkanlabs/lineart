# ADR-001: Extract Data Broker into Dedicated Microservice

**Status**: Accepted  
**Date**: 2025-11-06  
**Authors**: Engineering Team  
**Deciders**: Architecture Team

---

## Context

Currently, the Data Broker functionality is tightly coupled within the Vulkan Server/Engine monolith. The Data Broker is responsible for:

- Fetching data from external HTTP sources
- Managing intelligent caching with TTL
- Formatting responses (JSON, XML, CSV, plain text)
- Tracking data requests for analytics

**Current Architecture**:
```
Policy Run → Vulkan Server → DataSourceService → DataBroker (in-process)
                ↓
            App DB (DataSource + DataSourceEnvVar lookups)
```

**Problems with Current Design**:

1. **Tight Coupling**: Data Broker is embedded in the Engine, making it hard to scale independently
2. **Database Dependency**: Every data request requires DB lookups for data source specs and credentials
3. **Latency**: DB queries add 10-50ms per request
4. **Scalability**: Cannot scale data fetching independently from policy execution
5. **Resource Contention**: Heavy data fetching impacts policy orchestration performance
6. **Deployment Coupling**: Changes to data fetching logic require full Engine redeployment

**Current Code Locations**:
- `vulkan-engine/vulkan_engine/data/broker.py` - DataBroker class
- `vulkan-engine/vulkan_engine/services/data_source.py` - DataSourceService
- `vulkan-server/vulkan_server/routers/internal.py` - `/internal/data-broker` endpoint

---

## Decision

We will **extract the Data Broker into a dedicated microservice** that:

1. **Receives complete data source specifications in the request payload** (eliminating DB lookups during execution)
2. **Maintains caching functionality** (DataObject storage and RunDataCache)
3. **Provides a standalone HTTP API** for data fetching
4. **Remains stateless** for horizontal scaling

**New Architecture**:
```
Policy Run → Vulkan Server → Data Broker Service (HTTP API)
                                    ↓
                            Cache DB (DataObject, RunDataCache)
                                    ↓
                            External APIs
```

---

## Proposed Design

### 1. Data Broker Service (New Microservice)

**Technology Stack**:
- **Framework**: FastAPI (consistent with Vulkan Server)
- **Language**: Python 3.12
- **Database**: PostgreSQL (shared or dedicated instance for cache)
- **Deployment**: Docker container, orchestrated via Compose/K8s

**API Endpoint**:

**POST** `/v1/fetch-data`

**Request Payload**:
```json
{
  "data_source_spec": {
    "data_source_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "github_user_api",
    "source": {
      "url": "https://api.github.com/users/{{ username }}",
      "method": "GET",
      "headers": {
        "Authorization": "Bearer {{ github_token }}",
        "Accept": "application/vnd.github.v3+json"
      },
      "params": {},
      "body": {},
      "timeout": 30,
      "retry": {
        "max_retries": 3,
        "backoff_factor": 0.5,
        "status_forcelist": [500, 502, 503, 504]
      },
      "response_type": "JSON"
    },
    "caching": {
      "enabled": true,
      "ttl": 3600
    }
  },
  "env_variables": {
    "github_token": "ghp_abc123..."
  },
  "configured_params": {
    "username": "octocat"
  },
  "run_id": "660f9511-f39c-52e5-b827-557766551111"
}
```

**Response**:
```json
{
  "data_object_id": "770fa622-g40d-63f6-c938-668877662222",
  "origin": "REQUEST",
  "key": "a3f2b1c9d8e7f6a5b4c3d2e1f0a9b8c7",
  "value": {
    "login": "octocat",
    "id": 583231,
    "name": "The Octocat"
  },
  "start_time": 1699564800.123,
  "end_time": 1699564800.456,
  "error": null
}
```

### 2. Service Structure

```
data-broker-service/
├── pyproject.toml
├── Dockerfile
├── data_broker_service/
│   ├── __init__.py
│   ├── app.py              # FastAPI app
│   ├── config.py           # Service configuration
│   ├── models.py           # Pydantic request/response models
│   ├── broker.py           # Core DataBroker logic (migrated)
│   ├── cache.py            # CacheManager (migrated)
│   ├── db.py               # Database models (DataObject, RunDataCache)
│   ├── exceptions.py       # Custom exceptions
│   └── routers/
│       └── data.py         # /v1/fetch-data endpoint
└── tests/
    ├── test_broker.py
    └── test_cache.py
```

### 3. Migration Strategy

**Phase 1: Extract and Containerize** (Week 1-2)
1. Create new `data-broker-service` directory
2. Copy and adapt code from `vulkan-engine/data/broker.py`
3. Create FastAPI app with `/v1/fetch-data` endpoint
4. Set up database connection for cache tables
5. Write unit tests for broker logic
6. Dockerize the service
7. Add to `docker-compose.dev.yaml`

**Phase 2: Update Vulkan Server** (Week 2-3)
1. Update `DataSourceService.request_data_from_broker()` to:
   - Fetch full `DataSourceSpec` from DB (one-time at start)
   - Fetch `DataSourceEnvVar` values from DB
   - Build complete request payload
   - Call Data Broker Service HTTP API
2. Keep existing `/internal/data-broker` endpoint as facade
3. Add HTTP client with retry logic
4. Update error handling to propagate broker service errors

**Phase 3: Testing and Validation** (Week 3-4)
1. Integration tests with real external APIs
2. Load testing to validate performance
3. Cache hit rate monitoring
4. Compare latency: old (in-process) vs. new (HTTP call)
5. Validate error handling and timeouts

**Phase 4: Deployment** (Week 4-5)
1. Deploy to staging environment
2. Run parallel (shadow mode) for validation
3. Gradual rollout to production
4. Monitor metrics and rollback plan
5. Deprecate old in-process broker code

### 4. Database Schema

The Data Broker Service will manage its own cache tables:

**DataObject** (migrated from Engine):
```sql
CREATE TABLE data_object (
    data_object_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL,
    key VARCHAR NOT NULL,
    value BYTEA NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX idx_data_object_key ON data_object(key);
CREATE INDEX idx_data_object_data_source ON data_object(data_source_id);
```

**RunDataCache** (migrated from Engine):
```sql
CREATE TABLE run_data_cache (
    key VARCHAR PRIMARY KEY,
    data_object_id UUID NOT NULL REFERENCES data_object(data_object_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Note**: `RunDataRequest` remains in Vulkan Engine DB for analytics (tracked by Vulkan Server after broker response).

### 5. Configuration

**Environment Variables**:
```bash
# Data Broker Service
DATA_BROKER_HOST=0.0.0.0
DATA_BROKER_PORT=6002
DATA_BROKER_DB_HOST=localhost
DATA_BROKER_DB_PORT=5432
DATA_BROKER_DB_NAME=data_broker
DATA_BROKER_DB_USER=broker_user
DATA_BROKER_DB_PASSWORD=secure_password
DATA_BROKER_LOG_LEVEL=INFO
```

**Docker Compose** (`docker-compose.dev.yaml`):
```yaml
services:
  data-broker:
    build:
      context: .
      dockerfile: images/data-broker/Dockerfile
    ports:
      - "6002:6002"
    env_file:
      - config/active/data-broker.env
    depends_on:
      data-broker-db:
        condition: service_healthy

  data-broker-db:
    image: postgres:16.3
    env_file:
      - config/active/data-broker-db.env
    volumes:
      - postgres_data_broker_db:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 10

volumes:
  postgres_data_broker_db:
```

---

## Consequences

### Positive

1. **Independent Scaling**: Scale data fetching independently from policy orchestration
2. **Reduced Latency**: Eliminate DB lookups during execution (spec passed in payload)
3. **Better Resource Isolation**: Heavy data fetching doesn't impact orchestration
4. **Simplified Deployment**: Deploy broker changes without touching Engine
5. **Clear Separation of Concerns**: Data fetching is isolated responsibility
6. **Horizontal Scalability**: Run multiple broker instances behind load balancer
7. **Technology Flexibility**: Can rewrite broker in different language if needed

### Negative

1. **Network Latency**: HTTP call adds ~5-20ms vs. in-process call
2. **Increased Complexity**: One more service to deploy and monitor
3. **Payload Size**: Full spec in payload increases request size (~1-5KB)
4. **Operational Overhead**: Another service to maintain, monitor, and debug
5. **Distributed Tracing**: Need to track requests across service boundaries
6. **Error Handling**: Network failures add new failure modes

### Neutral

1. **Credential Management**: Credentials still passed in payload (addressed in ADR-002)
2. **Cache Location**: Cache DB can be shared or dedicated (to be decided)
3. **Authentication**: Internal service-to-service auth (to be implemented)

---

## Risks and Mitigations

### Risk 1: Network Failures
**Mitigation**: 
- Implement retry logic with exponential backoff
- Set appropriate timeouts (30s default)
- Circuit breaker pattern for repeated failures

### Risk 2: Increased Latency
**Mitigation**:
- Use HTTP/2 for connection pooling
- Keep-alive connections to reduce handshake overhead
- Monitor P95/P99 latency and optimize
- Consider gRPC for lower latency (future)

### Risk 3: Payload Size
**Mitigation**:
- Compress payloads with gzip
- Monitor payload sizes and set limits (10MB max)
- Consider payload optimization (remove unused fields)

### Risk 4: Credential Exposure
**Mitigation**:
- Use TLS for all service-to-service communication
- Implement service-to-service authentication (mTLS or JWT)
- Audit log all credential usage
- Plan for ADR-002 (credential service) to eliminate credentials in payload

---

## Alternatives Considered

### Alternative 1: Keep In-Process, Optimize DB Queries
**Rejected**: Doesn't address scalability or separation of concerns. Still couples data fetching to orchestration.

### Alternative 2: Async Job Queue (Celery/RQ)
**Rejected**: Adds complexity of queue management. Doesn't provide synchronous response needed for policy execution.

### Alternative 3: Serverless Functions (Lambda/Cloud Functions)
**Rejected**: Cold start latency, vendor lock-in, harder to debug. Microservice gives more control.

### Alternative 4: Shared Library
**Rejected**: Doesn't solve resource contention or independent scaling. Still tightly coupled.

---

## Implementation Checklist

- [ ] Create `data-broker-service` directory structure
- [ ] Migrate `DataBroker` and `CacheManager` classes
- [ ] Create FastAPI app with `/v1/fetch-data` endpoint
- [ ] Set up database migrations for cache tables
- [ ] Write unit tests (>80% coverage)
- [ ] Create Dockerfile and add to docker-compose
- [ ] Update Vulkan Server to call broker service
- [ ] Add integration tests
- [ ] Set up monitoring and alerting
- [ ] Document API in OpenAPI spec
- [ ] Update architecture diagrams
- [ ] Write runbook for operations
- [ ] Deploy to staging
- [ ] Load test and validate performance
- [ ] Production deployment
- [ ] Deprecate old in-process broker code

---

## Success Metrics

- **Latency**: P95 latency < 100ms for cache hits, < 500ms for external requests
- **Availability**: 99.9% uptime
- **Cache Hit Rate**: Maintain current rate (>60%)
- **Throughput**: Handle 1000 req/s per instance
- **Error Rate**: < 0.1% for non-external errors
- **Deployment Time**: Broker changes deployable in < 5 minutes


---

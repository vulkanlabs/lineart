# ADR-002: Event-Driven Credential Service with Cache Invalidation

**Status**: Proposed (Future Work)  
**Date**: 2025-11-06  
**Authors**: Engineering Team  
**Deciders**: Architecture Team  
**Supersedes**: None  
**Depends On**: ADR-001 (Data Broker Microservice)

---

## Context

After implementing ADR-001 (Data Broker as a microservice), we will have eliminated database lookups for data source specifications by passing the complete spec in the request payload. However, this creates a **critical problem with credential management**:

**The Stale Credential Problem**:

When credentials are embedded directly in the request payload:

1. **Long-running workflows** (hours/days) will use stale credentials if a user updates their API token mid-execution
2. **No propagation mechanism** exists to update credentials for in-flight policy runs
3. **Security risk**: Credentials remain valid in payloads even after user revokes them
4. **Audit gap**: Cannot track when stale credentials are used

**Example Scenario**:
```
Time 0:00 - Policy run starts with github_token="abc123"
Time 1:30 - User rotates token to "xyz789" in UI
Time 2:00 - Policy run tries to fetch data with "abc123" → FAILS (401 Unauthorized)
```

**Current Architecture (Post ADR-001)**:
```
Vulkan Server → Data Broker Service
     ↓
  Fetch DataSource + Credentials from DB
     ↓
  Embed credentials in payload
     ↓
  Send to Data Broker (credentials may be stale)
```

---

## Decision

We will implement an **Event-Driven Credential Service** that:

1. **Separates credential storage** from data source configuration
2. **Resolves credentials on-demand** at the Data Broker Service (not embedded in payload)
3. **Uses distributed caching** with short TTL to minimize latency
4. **Publishes invalidation events** when credentials are updated
5. **Ensures fresh credentials** for all requests, including long-running workflows

**New Architecture**:
```
┌─────────────────┐
│  Vulkan Server  │
│  (Orchestrator) │
└────────┬────────┘
         │ POST /v1/fetch-data
         │ {spec, credential_refs, params}
         ▼
┌─────────────────────────┐      ┌──────────────────┐
│  Data Broker Service    │◄─────┤ Credential Cache │
│                         │      │  (Redis, 60s TTL)│
└────────┬────────────────┘      └────────▲─────────┘
         │                                │
         │ GET /v1/credentials/{id}       │ Invalidate
         ▼                                │
┌─────────────────────────┐      ┌──────────────────┐
│  Credential Service     │─────►│   Event Bus      │
│  (Microservice)         │      │  (Redis Pub/Sub) │
└─────────────────────────┘      └──────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Credential DB          │
│  (DataSourceEnvVar)     │
└─────────────────────────┘
```

---

## Proposed Design

### 1. Credential References (Not Values)

Instead of embedding credential values in the payload, pass **references**:

**Request Payload** (from Vulkan Server to Data Broker):
```json
{
  "data_source_spec": {
    "data_source_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "github_user_api",
    "source": {
      "url": "https://api.github.com/users/{{ username }}",
      "method": "GET",
      "headers": {
        "Authorization": "Bearer {{ github_token }}"
      },
      "response_type": "JSON"
    },
    "caching": {
      "enabled": true,
      "ttl": 3600
    }
  },
  "credential_refs": {
    "github_token": {
      "data_source_id": "550e8400-e29b-41d4-a716-446655440000",
      "var_name": "github_token"
    }
  },
  "configured_params": {
    "username": "octocat"
  },
  "run_id": "660f9511-f39c-52e5-b827-557766551111"
}
```

### 2. Credential Service (New Microservice)

**Responsibilities**:
- Store and retrieve credentials (DataSourceEnvVar)
- Validate credential access (authorization)
- Publish credential update events
- Audit credential access
- Support credential rotation

**API Endpoints**:

**GET** `/v1/credentials/{data_source_id}/{var_name}`

**Request Headers**:
```
Authorization: Bearer <service-token>
X-Project-ID: <project-uuid>
```

**Response**:
```json
{
  "data_source_id": "550e8400-e29b-41d4-a716-446655440000",
  "var_name": "github_token",
  "value": "ghp_abc123...",
  "version": "v3",
  "updated_at": "2025-11-06T10:30:00Z"
}
```

**PUT** `/v1/credentials/{data_source_id}/{var_name}`

**Request**:
```json
{
  "value": "ghp_xyz789...",
  "nullable": false
}
```

**Response**:
```json
{
  "data_source_id": "550e8400-e29b-41d4-a716-446655440000",
  "var_name": "github_token",
  "version": "v4",
  "updated_at": "2025-11-06T11:00:00Z"
}
```

**Side Effect**: Publishes `CredentialUpdatedEvent` to event bus.

### 3. Data Broker Service Updates

The Data Broker Service will resolve credentials on-demand:

```python
class DataBrokerService:
    def __init__(
        self, 
        credential_cache: RedisCache, 
        credential_client: CredentialServiceClient,
        event_bus: EventBus
    ):
        self.credential_cache = credential_cache
        self.credential_client = credential_client
        self.event_bus = event_bus
        
        # Subscribe to credential update events
        self.event_bus.subscribe(
            "credential.updated", 
            self.on_credential_updated
        )
    
    async def fetch_data(self, request: FetchDataRequest):
        # Resolve credentials (cache-first)
        env_variables = await self.resolve_credentials(
            request.credential_refs
        )
        
        # Proceed with data fetch
        broker = DataBroker(spec=request.data_source_spec)
        return broker.get_data(
            request.configured_params, 
            env_variables
        )
    
    async def resolve_credentials(
        self, 
        credential_refs: dict
    ) -> dict:
        env_variables = {}
        
        for var_name, ref in credential_refs.items():
            cache_key = f"cred:{ref.data_source_id}:{var_name}"
            
            # Try cache first (60s TTL)
            cached_value = await self.credential_cache.get(cache_key)
            
            if cached_value is not None:
                env_variables[var_name] = cached_value
            else:
                # Cache miss, fetch from Credential Service
                credential = await self.credential_client.get_credential(
                    data_source_id=ref.data_source_id,
                    var_name=var_name
                )
                
                # Cache for 60 seconds
                await self.credential_cache.set(
                    cache_key, 
                    credential.value, 
                    ttl=60
                )
                
                env_variables[var_name] = credential.value
        
        return env_variables
    
    async def on_credential_updated(self, event: CredentialUpdatedEvent):
        """Invalidate cache when credential is updated."""
        cache_key = f"cred:{event.data_source_id}:{event.var_name}"
        await self.credential_cache.delete(cache_key)
        
        self.logger.info(
            f"Invalidated credential cache: {event.data_source_id}:{event.var_name}"
        )
```

### 4. Event Bus (Redis Pub/Sub)

**Event Schema**:
```json
{
  "event_type": "credential.updated",
  "event_id": "880fb733-h51e-74g7-d049-779988773333",
  "timestamp": "2025-11-06T11:00:00Z",
  "data": {
    "data_source_id": "550e8400-e29b-41d4-a716-446655440000",
    "var_name": "github_token",
    "version": "v4",
    "project_id": "440e5500-e29b-41d4-a716-446655440000"
  }
}
```

**Redis Pub/Sub Channel**: `credential.events`

**Publishers**: Credential Service (on PUT/DELETE)  
**Subscribers**: All Data Broker Service instances

### 5. Credential Cache (Redis)

**Configuration**:
- **TTL**: 60 seconds (balance between freshness and performance)
- **Eviction Policy**: LRU (Least Recently Used)
- **Max Memory**: 256MB per instance
- **Persistence**: Optional (cache can be rebuilt from Credential Service)

**Cache Key Format**: `cred:{data_source_id}:{var_name}`

**Example**:
```
cred:550e8400-e29b-41d4-a716-446655440000:github_token → "ghp_abc123..."
```

**Cache Hit Rate Target**: >95% (with 60s TTL and typical workflow patterns)

### 6. Service Structure

**Credential Service**:
```
credential-service/
├── pyproject.toml
├── Dockerfile
├── credential_service/
│   ├── __init__.py
│   ├── app.py              # FastAPI app
│   ├── config.py           # Service configuration
│   ├── models.py           # Pydantic models
│   ├── db.py               # Database models (DataSourceEnvVar)
│   ├── events.py           # Event publishing
│   ├── auth.py             # Service-to-service auth
│   ├── audit.py            # Audit logging
│   └── routers/
│       └── credentials.py  # CRUD endpoints
└── tests/
    ├── test_credentials.py
    └── test_events.py
```

---

## Implementation Strategy

### Phase 1: Credential Service (Weeks 1-3)

1. Create `credential-service` microservice
2. Implement CRUD endpoints for credentials
3. Set up database connection (reuse App DB or dedicated)
4. Add service-to-service authentication (JWT or mTLS)
5. Implement audit logging for all credential access
6. Write unit and integration tests
7. Dockerize and add to docker-compose

### Phase 2: Event Bus Integration (Weeks 3-4)

1. Set up Redis Pub/Sub infrastructure
2. Implement event publishing in Credential Service
3. Define event schemas and versioning
4. Add event bus client library
5. Test event delivery and reliability

### Phase 3: Data Broker Updates (Weeks 4-5)

1. Add credential cache (Redis) to Data Broker Service
2. Implement credential resolution logic
3. Subscribe to credential update events
4. Update request payload to use credential refs
5. Add cache metrics and monitoring

### Phase 4: Vulkan Server Updates (Weeks 5-6)

1. Update `DataSourceService` to build credential refs
2. Remove credential values from payload
3. Add credential service client
4. Update error handling for credential failures
5. Add integration tests

### Phase 5: Testing and Rollout (Weeks 6-8)

1. End-to-end testing with credential rotation
2. Load testing and cache hit rate validation
3. Chaos testing (event bus failures, cache failures)
4. Gradual rollout to production
5. Monitor metrics and optimize TTL

---

## Consequences

### Positive

1. **Fresh Credentials**: Always uses latest credentials, even for long-running workflows
2. **Immediate Propagation**: Credential updates propagate in <1 second via events
3. **Security**: Credentials not embedded in payloads or logs
4. **Auditability**: Track all credential access and updates
5. **Scalability**: Credential cache reduces DB load by >95%
6. **Separation of Concerns**: Credential management is isolated responsibility
7. **Credential Rotation**: Supports automated rotation without workflow disruption

### Negative

1. **Increased Complexity**: Two new components (Credential Service + Event Bus)
2. **Network Latency**: Credential resolution adds ~5-10ms (cache hit) or ~20-50ms (cache miss)
3. **Cache Consistency**: Risk of stale cache if events are lost (mitigated by TTL)
4. **Operational Overhead**: More services to monitor and maintain
5. **Event Bus Dependency**: System depends on Redis Pub/Sub availability

### Neutral

1. **Cache TTL**: 60s is a trade-off (can be tuned based on metrics)
2. **Event Delivery**: At-least-once delivery (idempotent cache invalidation)
3. **Credential Storage**: Still in same DB (can be moved to secret manager later)

---

## Risks and Mitigations

### Risk 1: Event Bus Failure
**Impact**: Cache invalidation events not delivered, stale credentials used for up to 60s.

**Mitigations**:
- Short TTL (60s) limits stale credential window
- Monitor event bus health and alert on failures
- Fallback: Force cache invalidation on credential service restart
- Future: Add event persistence/replay for reliability

### Risk 2: Cache Stampede
**Impact**: Many Data Broker instances request same credential simultaneously on cache miss.

**Mitigations**:
- Implement cache locking (Redis SETNX)
- Stagger cache expiry with jitter
- Pre-warm cache for frequently used credentials

### Risk 3: Credential Service Downtime
**Impact**: Data Broker cannot resolve credentials, all data fetches fail.

**Mitigations**:
- High availability: Run multiple Credential Service instances
- Circuit breaker: Fail fast and return cached credentials if available
- Graceful degradation: Allow stale cached credentials during outage
- Monitor SLA and alert on degradation

### Risk 4: Increased Latency
**Impact**: Credential resolution adds latency to data fetches.

**Mitigations**:
- Optimize cache hit rate (target >95%)
- Use HTTP/2 keep-alive for Credential Service calls
- Monitor P95/P99 latency and optimize
- Consider gRPC for lower latency

---

## Alternatives Considered

### Alternative 1: Credential Versioning (No Event Bus)

**Design**: Include credential version in payload, validate at Data Broker.

**Rejected**: 
- Requires version lookup (still a DB call)
- Doesn't solve stale credential problem (fails instead of updating)
- Adds retry complexity to orchestrator

### Alternative 2: Short-Lived Tokens (JWT)

**Design**: Issue short-lived tokens (1 hour), refresh as needed.

**Rejected**:
- Requires token refresh logic in long-running workflows
- Adds token service complexity
- Doesn't solve user-initiated credential updates

### Alternative 3: Embed Credentials with Expiry

**Design**: Embed credentials in payload with expiry timestamp, refetch on expiry.

**Rejected**:
- Still uses stale credentials until expiry
- Adds complexity to Data Broker (refetch logic)
- Doesn't handle user-initiated updates

### Alternative 4: Polling (No Event Bus)

**Design**: Data Broker polls Credential Service for updates.

**Rejected**:
- High latency (polling interval vs. event propagation)
- Inefficient (many unnecessary polls)
- Doesn't scale well

---

## Success Metrics

- **Credential Freshness**: 100% of requests use latest credentials (within 60s)
- **Cache Hit Rate**: >95% for credential lookups
- **Event Propagation Latency**: <1 second from update to cache invalidation
- **Credential Service Availability**: 99.9% uptime
- **Data Broker Latency Impact**: <10ms P95 increase for credential resolution
- **Audit Coverage**: 100% of credential access logged

---

## Open Questions

1. **Credential Encryption**: Should credentials be encrypted at rest in DB?
   - **Recommendation**: Yes, use application-level encryption or DB encryption
   
2. **Secret Manager Integration**: Should we use external secret manager (AWS Secrets Manager, HashiCorp Vault)?
   - **Recommendation**: Phase 2 enhancement, after validating architecture

3. **Event Bus Technology**: Redis Pub/Sub vs. Kafka vs. RabbitMQ?
   - **Recommendation**: Start with Redis Pub/Sub (simpler), migrate to Kafka if needed

4. **Cache Persistence**: Should credential cache be persistent?
   - **Recommendation**: No, cache can be rebuilt from Credential Service

5. **Multi-Region**: How to handle credential cache in multi-region deployments?
   - **Recommendation**: Regional caches with event replication (future work)

---

## Related ADRs

- **ADR-001**: Data Broker Microservice (prerequisite)

---

## References

- [Data Broker Technical Documentation](../architecture/data-broker.md)
- [ADR-001: Data Broker Microservice](./ADR-001-data-broker-microservice.md)
- [Redis Pub/Sub Documentation](https://redis.io/docs/manual/pubsub/)
- [Event-Driven Architecture Patterns](https://martinfowler.com/articles/201701-event-driven.html)


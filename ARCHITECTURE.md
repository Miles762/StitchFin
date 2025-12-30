# VocalBridge Ops - Architecture Documentation

## Table of Contents

1. [High-Level Design (HLD)](#high-level-design-hld)
2. [Low-Level Design (LLD)](#low-level-design-lld)

---

## High-Level Design (HLD)

### System Architecture

```
┌─────────────────────────────────────────┐
│         CLIENT LAYER                     │
│  (React Dashboard, API Clients)          │
└───────────────┬─────────────────────────┘
                │ HTTP/REST
                ▼
┌─────────────────────────────────────────┐
│       API GATEWAY (FastAPI)              │
│  - Auth (API Key validation)             │
│  - Correlation ID Tracking               │
│  - CORS & Error Handling                 │
└───────────────┬─────────────────────────┘
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
    ┌────┐  ┌──────┐  ┌────────┐
    │Tenant│ │Agent │  │Session │
    │ API  │ │ API  │  │  API   │
    └────┘  └──────┘  └────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│      BUSINESS LOGIC LAYER                │
│  - Message Handler                       │
│  - Resilient Caller (Retry/Fallback)    │
│  - Billing Service                       │
│  - Tool Executor                         │
│  - Voice Handler (STT/TTS)               │
└───────────────┬─────────────────────────┘
                │
        ┌───────┼───────┐
        ▼       ▼       ▼
    ┌────┐  ┌─────┐  ┌──────┐
    │ DB │  │Cache│  │OpenAI│
    └────┘  └─────┘  └──────┘
```

### Component Responsibilities

- **Client Layer**: React dashboard + external API access
- **API Gateway**: Request validation, authentication, routing, middleware
- **Business Logic**: Message orchestration, vendor abstraction, reliability, billing
- **Data Layer**: PostgreSQL (primary), Redis (cache), OpenAI APIs (STT/TTS)

---

## Low-Level Design (LLD)

### Database Schema

**9 Core Tables:**

```sql
-- Multi-tenant root
tenants (id, name, api_key, created_at, updated_at)

-- Agent configurations
agents (id, tenant_id, name, primary_provider, fallback_provider,
        system_prompt, enabled_tools, config)

-- Conversation management
sessions (id, tenant_id, agent_id, customer_id, channel, metadata)
messages (id, session_id, role, content, provider_used,
          tokens_in, tokens_out, latency_ms, correlation_id)

-- Billing & audit
usage_events (id, tenant_id, provider, tokens_in, tokens_out, cost_usd)
provider_calls (id, correlation_id, provider, attempt_number, status, latency_ms)
tool_executions (id, tenant_id, tool_name, parameters, result, status)

-- Infrastructure
idempotency_keys (key, tenant_id, response, expires_at)
voice_artifacts (id, session_id, artifact_type, audio_data, transcript)
```

**Design Principles:**
- UUID primary keys
- JSONB for flexible metadata
- Indexed foreign keys (tenant_id, session_id, correlation_id)
- CASCADE deletes for automatic cleanup
- Decimal(10,6) precision for cost calculations

### Request Flow

```
1. Client Request → POST /api/sessions/{id}/messages
   Headers: X-API-Key, Idempotency-Key, X-Correlation-ID

2. Middleware → Auth (validate API key) + Correlation ID

3. Idempotency Check → Return cached if exists

4. Message Handler → Load agent config

5. Resilient Caller → Primary vendor (10s timeout)
   ↓ (on failure)
   Retry 3x (exponential backoff: 1s, 2s, 4s)
   ↓ (on failure)
   Fallback to secondary vendor

6. Tool Execution → If enabled (invoice_lookup)

7. Billing → Calculate cost, log to usage_events

8. Cache Response → Store with 24h TTL

9. Return → 201 Created + correlation_id
```

### Voice Channel Flow

```
Audio Upload → Whisper STT → Agent Processing → OpenAI TTS → Store MP3 → Return URL
```

### Multi-Tenancy

**Row-Level Isolation:**
```python
# All queries filtered by tenant_id
agents = db.query(Agent).filter(Agent.tenant_id == tenant.id).all()
```

**API Key Auth:**
```python
api_key = f"sk_{secrets.token_urlsafe(32)}"  # Cryptographically secure
```

### Vendor Adapter Pattern

**Strategy Pattern:**
```python
class VendorAdapter(ABC):
    async def send_message(self, request) -> Dict
    def normalize_response(self, raw) -> NormalizedResponse
```

**Implementations:**
- VendorA: 10% failure rate (HTTP 500)
- VendorB: 15% rate limits (HTTP 429)

### Reliability (3 Layers)

1. **Timeout**: 10 seconds max
2. **Retry**: 3 attempts, exponential backoff
3. **Fallback**: Switch to secondary vendor

### Idempotency

```python
# Check cache before processing
if idempotency_key:
    cached = get_cached_response(key)
    if cached: return cached  # No re-processing
```

**Storage**: Database table, 24h TTL

### Billing

**Pricing:**
- VendorA: $0.002 per 1K tokens
- VendorB: $0.003 per 1K tokens

**Calculation:**
```python
cost = ((tokens_in + tokens_out) / 1000) * price
# Stored as Decimal(10,6) in usage_events table
```

### Observability

- **Correlation IDs**: Track requests end-to-end
- **Structured Logs**: JSON format (timestamp, level, correlation_id, metrics)
- **Audit Tables**: provider_calls, tool_executions

### Scaling Strategy

**Horizontal:**
- Stateless FastAPI pods
- Load balancer
- PostgreSQL read replicas
- Redis cache layer

**Database:**
- Connection pooling (pool_size=20, max_overflow=40)
- Table partitioning by tenant_id
- Indexes on all foreign keys

---



# VocalBridge Ops - Architecture Documentation

## Table of Contents

1. [System Design Overview](#system-design-overview)
2. [Database Schema](#database-schema)
3. [Request Flow](#request-flow)
4. [Multi-Tenancy Strategy](#multi-tenancy-strategy)
5. [Vendor Adapter Pattern](#vendor-adapter-pattern)
6. [Reliability & Failure Handling](#reliability--failure-handling)
7. [Idempotency Implementation](#idempotency-implementation)
8. [Billing & Metering](#billing--metering)
9. [Tool Framework](#tool-framework)
10. [Voice Channel Architecture](#voice-channel-architecture)
11. [Scaling Strategy](#scaling-strategy)
12. [Security](#security)
13. [Trade-offs & Decisions](#trade-offs--decisions)

---

## System Design Overview

### Three-Tier Architecture

```
┌──────────────────────────────────────────┐
│  CLIENT LAYER (React + Direct API)       │
│  - React Dashboard (localhost:5173)      │
│  - External API clients (curl, etc.)     │
└───────────────┬──────────────────────────┘
                │ HTTP/REST
                ▼
┌──────────────────────────────────────────┐
│  API GATEWAY (FastAPI + Middleware)      │
│  - Auth (API key validation)             │
│  - Correlation ID tracking               │
│  - CORS + Error handling                 │
└───────────────┬──────────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│Tenants  │ │Agents   │ │Sessions │
│Agents   │ │Sessions │ │Voice    │
│Analytics│ │Messages │ │Analytics│
└────┬────┘ └────┬────┘ └────┬────┘
     │           │           │
     └───────────┴───────────┘
                 │
┌────────────────┴────────────────────────┐
│  BUSINESS LOGIC                         │
│  - Message Handler (orchestration)      │
│  - Resilient Caller (retry/fallback)    │
│  - Billing Service (cost tracking)      │
│  - Tool Executor (plugin system)        │
│  - Voice Handler (STT/TTS pipeline)     │
└─────────────────────────────────────────┘
                 │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
┌──────────┐ ┌─────────┐ ┌────────────┐
│PostgreSQL│ │ Redis   │ │OpenAI APIs │
│(Primary) │ │(Cache)  │ │(Whisper/TTS)│
└──────────┘ └─────────┘ └────────────┘
```

### Component Responsibilities

**API Layer**: Request validation, authentication, routing, error handling
**Business Logic**: Message orchestration, vendor abstraction, billing, tool execution
**Data Layer**: Persistent storage (PostgreSQL), caching (Redis), external services (OpenAI)

---

## Database Schema

### Core Tables (9 total)

```sql
-- Multi-tenant isolation root
tenants (id, name, api_key, created_at, updated_at)
  INDEX: api_key (for auth lookups)

-- Agent configurations
agents (id, tenant_id, name, primary_provider, fallback_provider,
        system_prompt, enabled_tools, config)
  INDEX: tenant_id
  CASCADE: ON DELETE CASCADE from tenants

-- Conversation sessions
sessions (id, tenant_id, agent_id, customer_id, channel, metadata)
  INDEX: tenant_id, agent_id

-- Message transcripts
messages (id, session_id, role, content, provider_used,
          tokens_in, tokens_out, latency_ms, tools_called, correlation_id)
  INDEX: session_id, correlation_id

-- Billing records
usage_events (id, tenant_id, agent_id, session_id, message_id,
              provider, tokens_in, tokens_out, cost_usd, event_type)
  INDEX: tenant_id, created_at

-- Reliability audit trail
provider_calls (id, tenant_id, session_id, correlation_id, provider,
                attempt_number, status, http_status, latency_ms, error_message)
  INDEX: correlation_id

-- Tool execution logs
tool_executions (id, tenant_id, agent_id, session_id, message_id,
                 tool_name, parameters, result, status, latency_ms)

-- Request deduplication
idempotency_keys (key, tenant_id, response, created_at, expires_at)
  INDEX: expires_at (for cleanup)

-- Voice artifacts storage
voice_artifacts (id, tenant_id, session_id, message_id, artifact_type,
                 audio_data, duration_seconds, transcript, provider, latency_ms)
  INDEX: session_id, message_id
```

### Key Design Principles

- **UUID primary keys**: Prevents enumeration attacks, enables distributed generation
- **JSONB fields**: Flexible metadata storage without schema changes (config, tools_called, metadata)
- **Indexes**: Optimized for common query patterns (tenant scoping, correlation tracking)
- **Cascading deletes**: Automatic cleanup when tenant is deleted
- **Decimal precision**: 6 decimal places for cost_usd (avoids floating point errors)

---

## Request Flow

### Text Message Processing (12 Steps)

```
1. Client → POST /api/sessions/{id}/messages
   Headers: X-API-Key, Idempotency-Key, X-Correlation-ID

2. CorrelationIDMiddleware → Generate/extract correlation ID

3. AuthMiddleware → Validate API key → Load tenant

4. Idempotency check → Return cached response if exists

5. MessageHandler → Load agent config from DB

6. ResilientCaller → Call primary vendor (VendorA)
   - Timeout: 10s
   - Retries: 3 attempts with exponential backoff (1s, 2s, 4s)
   - On failure: Try fallback vendor (VendorB)

7. Tool detection → Execute if "invoice" in message + tool enabled

8. Create assistant message → INSERT into messages table

9. BillingService → Calculate cost → INSERT usage_event

10. Cache response → INSERT idempotency_keys (TTL: 24h)

11. Return response → 201 Created + correlation_id header

12. All attempts logged to provider_calls table
```

### Voice Message Processing (STT → Agent → TTS)

```
1. Client → POST /api/sessions/{id}/voice/message
   Body: multipart/form-data (audio file)

2. Validate: session.channel == 'voice' + file size < 25MB

3. STT → OpenAI Whisper API
   - Transcribe audio → text
   - Store in voice_artifacts (artifact_type='audio_in')

4. Process text → Same as text message flow (steps 5-9)

5. TTS → OpenAI TTS API
   - Synthesize assistant response → MP3
   - Store in voice_artifacts (artifact_type='audio_out')

6. Return: user_message + assistant_message + audio_download_url + latencies
```

---

## Multi-Tenancy Strategy

### Row-Level Isolation (Chosen Approach)

**Implementation:**
```python
# All queries MUST filter by tenant_id
agents = db.query(Agent).filter(
    Agent.tenant_id == tenant.id  # Enforced by auth middleware
).all()
```

**Authentication Flow:**
```python
def get_current_tenant(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Tenant:
    tenant = db.query(Tenant).filter(
        Tenant.api_key == x_api_key
    ).first()
    if not tenant:
        raise UnauthorizedException("Invalid API key")
    return tenant
```

**API Key Format:** `sk_{secrets.token_urlsafe(32)}` (cryptographically secure)

### Alternative Approaches (Rejected)

| Approach | Why Rejected |
|----------|--------------|
| **Database per tenant** | Complex management, expensive, migration nightmares |
| **Schema per tenant** | Schema proliferation, harder to query across tenants |
| **Row-level (chosen)** | ✅ Simple, scalable, requires query discipline |

---

## Vendor Adapter Pattern

### Strategy Pattern Implementation

```python
class VendorAdapter(ABC):
    @abstractmethod
    async def send_message(self, request: VendorRequest) -> Dict[str, Any]:
        """Return raw vendor-specific response"""
        pass

    @abstractmethod
    def normalize_response(self, raw: Dict) -> NormalizedResponse:
        """Convert vendor format to common format"""
        pass
```

### VendorA vs VendorB Differences

| Aspect | VendorA | VendorB |
|--------|---------|---------|
| **Response format** | `{outputText, tokensIn, tokensOut}` | `{choices[].message.content, usage{}}` |
| **Failure mode** | 10% HTTP 500 errors | 15% rate limits (HTTP 429) |
| **Normalization** | `raw["outputText"]` | `raw["choices"][0]["message"]["content"]` |

### Factory Pattern

```python
def get_vendor_adapter(provider: str) -> VendorAdapter:
    vendors = {"vendorA": VendorA, "vendorB": VendorB}
    return vendors[provider]()
```

**Benefits**: Add new vendors without changing business logic, easy to mock for testing, uniform interface for rest of system.

---

## Reliability & Failure Handling

### Three-Layer Resilience: Timeout → Retry → Fallback

#### Layer 1: Timeout Wrapper
```python
async def _call_with_timeout(vendor, request):
    return await asyncio.wait_for(
        vendor.call(request),
        timeout=10  # 10 second timeout
    )
```

#### Layer 2: Exponential Backoff Retry
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((
        VendorAHTTPError, VendorBRateLimitError, VendorCallTimeout
    ))
)
async def _call_with_retry(vendor, request, attempt_number):
    # Log each attempt to provider_calls table
    pass
```

**Retry schedule**: Attempt 1 (immediate) → 1s → 2s → 4s (exponential: 2^n)

#### Layer 3: Fallback Provider
```python
async def call_with_fallback(primary, fallback, request):
    try:
        return await call_with_retry(primary, request)
    except Exception as primary_error:
        if not fallback:
            raise AllVendorsFailed(primary_error)
        return await call_with_retry(fallback, request)
```

### Failure Scenarios Matrix

| Scenario | Logged Events | Outcome |
|----------|---------------|---------|
| VendorA succeeds immediately | 1 success | Response returned |
| VendorA timeout → retry succeeds | 1 retry + 1 success | Response returned |
| VendorA fails 3x, no fallback | 3 retries + 1 error | Error raised |
| VendorA fails 3x, fallback succeeds | 3 retries + 1 fallback + 1 success | Response from VendorB |
| Both vendors fail | All attempts | AllVendorsFailed exception |

---

## Idempotency Implementation

### Problem: Network retries → duplicate messages → double billing

### Solution: Request deduplication

```python
async def send_message(idempotency_key: Optional[str]):
    if idempotency_key:
        cached = get_cached_response(idempotency_key, tenant_id)
        if cached:
            return cached  # Return immediately, skip processing

    response = await handle_message(...)
    cache_response(idempotency_key, response, ttl_hours=24)
    return response
```

### Storage Options

**Database (current):**
```sql
CREATE TABLE idempotency_keys (
    key VARCHAR(255) PRIMARY KEY,
    tenant_id UUID NOT NULL,  -- Scope to tenant
    response JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL
);
```

**Redis (optional enhancement):**
```python
redis.setex(f"idempotency:{tenant_id}:{key}", 86400, json.dumps(response))
```

### Guarantees
- Exactly-once semantics (same key = same response)
- No double-billing (only one usage_event)
- 24-hour window (keys auto-expire)

---

## Billing & Metering

### Pricing Model

```python
PRICING = {
    "vendorA": {"input_tokens": Decimal("0.002"), "output_tokens": Decimal("0.002")},
    "vendorB": {"input_tokens": Decimal("0.003"), "output_tokens": Decimal("0.003")},
}
```

### Cost Calculation (6 decimal precision)

```python
def calculate_cost(provider: str, tokens_in: int, tokens_out: int) -> Decimal:
    pricing = PRICING[provider]
    input_cost = (Decimal(tokens_in) / 1000) * pricing["input_tokens"]
    output_cost = (Decimal(tokens_out) / 1000) * pricing["output_tokens"]
    return (input_cost + output_cost).quantize(Decimal('0.000001'))
```

**Example**: VendorA, 500 in + 300 out = (0.5 × $0.002) + (0.3 × $0.002) = **$0.0016**

### Usage Event Creation

```python
usage_event = UsageEvent(
    tenant_id=tenant_id,
    provider=provider,
    tokens_in=500,
    tokens_out=300,
    cost_usd=Decimal("0.0016"),
    event_type="message"
)
```

### Analytics Queries

**Total cost per tenant:**
```sql
SELECT tenant_id, SUM(cost_usd) FROM usage_events GROUP BY tenant_id;
```

**Provider breakdown:**
```sql
SELECT provider, COUNT(*) as messages, SUM(cost_usd) as cost
FROM usage_events WHERE tenant_id = ? GROUP BY provider;
```

---

## Tool Framework

### Abstract Tool Interface

```python
class Tool(ABC):
    @abstractmethod
    async def execute(self, params: Dict, context: Dict) -> Dict:
        pass
```

### Invoice Lookup Example

```python
class InvoiceLookupTool(Tool):
    INVOICES = {
        "INV-TC-001": {"amount": 15000.00, "status": "paid"},
        "INV-HF-001": {"amount": 45000.00, "status": "paid"}
    }

    async def execute(self, params, context):
        invoice_id = params["invoice_id"]
        tenant_id = context["tenant_id"]

        # Tenant isolation: Only return invoices for current tenant
        invoice = self.INVOICES.get(invoice_id)
        if invoice and invoice["tenant_id"] == tenant_id:
            return {"success": True, "invoice": invoice}
        return {"success": False, "error": "Not found"}
```

### Audit Trail
All executions logged to `tool_executions` table with parameters, result, status, latency.

---

## Voice Channel Architecture

### Pipeline: Audio → STT → Agent → TTS → Audio

```
Browser MediaRecorder → WebM/MP3 → FastAPI Endpoint
    ↓
OpenAI Whisper (STT) → Transcript text
    ↓
Agent Processing (VendorA/B) → Response text
    ↓
OpenAI TTS → MP3 audio
    ↓
PostgreSQL BYTEA → Download endpoint
```

### Voice Services

**STT Service:**
```python
class STTService:
    model = "whisper-1"

    async def transcribe(audio_file):
        transcript = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
        return {"text": transcript.text, "duration": transcript.duration}
```

**TTS Service:**
```python
class TTSService:
    model = "tts-1"  # Fast, low latency
    voice = "alloy"

    async def synthesize(text):
        response = openai.audio.speech.create(
            model="tts-1", voice="alloy", input=text, response_format="mp3"
        )
        return {"audio_data": response.content}
```

### Storage Strategy

**Current**: PostgreSQL BYTEA (good for <10MB files)
**Future**: S3/GCS for larger files (store URL reference in DB)

---

## Scaling Strategy

### Horizontal Scaling

```
Load Balancer → [App Pod 1, App Pod 2, ..., App Pod N]
                        ↓
                 [PostgreSQL Primary + Read Replicas]
                 [Redis Cache]
```

**Requirements:**
- Stateless FastAPI app (no in-memory state)
- Database connection pooling (20 pool size, 40 max overflow)
- Redis for shared cache (idempotency, rate limiting)

### Database Optimizations

**Read replicas**: Analytics queries → replicas, Writes → primary
**Partitioning**: Partition `usage_events` by tenant_id
**Indexing**: All foreign keys + common query filters indexed

### Performance Targets

| Metric | Target |
|--------|--------|
| P95 latency | <500ms |
| Throughput | 1000 req/s |
| Uptime | 99.9% |

---

## Security

### API Key Security
- **Generation**: `secrets.token_urlsafe(32)` (cryptographically secure)
- **Storage**: Plaintext in DB (consider hashing for production)
- **Transmission**: HTTPS only (not enforced in MVP)

### SQL Injection Prevention
- SQLAlchemy ORM (parameterized queries by default)
- No raw SQL queries

### Input Validation
- Pydantic schemas for all requests
- Type checking enforced

### CORS Policy
```python
allow_origins=["http://localhost:5173"]  # Whitelist only, no wildcards
```

---

## Trade-offs & Decisions

### 1. PostgreSQL vs SQLite
**Chosen**: PostgreSQL
**Reason**: Production-ready, ACID compliance, JSON support, read replicas
**Trade-off**: Requires Docker setup (worth it for realism)

### 2. In-Process Mocks vs HTTP Mocks
**Chosen**: In-process Python mocks
**Reason**: Faster development, easy failure simulation, demonstrates adapter pattern
**Trade-off**: Less realistic (real vendors use HTTP)

### 3. Database vs Redis for Idempotency
**Chosen**: Database (Redis optional)
**Reason**: One less dependency, simpler deployment
**Trade-off**: Slightly slower (negligible at MVP scale)

### 4. Sync vs Async Processing
**Chosen**: Synchronous (no job queue)
**Reason**: Simpler architecture, meets requirements
**Trade-off**: Client waits for response (acceptable for chat)

### 5. Full React UI
**Chosen**: Complete React dashboard
**Reason**: Better demo, voice requires frontend, production-ready
**Outcome**: React 18 + TypeScript + TailwindCSS + Recharts

---

**Document Version**: 2.0
**Last Updated**: December 30, 2025
**Author**: VocalBridge Ops Team

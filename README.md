# VocalBridge Ops - Multi-Tenant Agent Gateway

A production-ready SaaS platform for managing AI agents with multi-tenant isolation, vendor abstraction, reliability features (timeouts/retries/fallback), and comprehensive usage billing.

## 🎯 Project Overview

VocalBridge Ops is a backend service + dashboard that enables businesses (tenants) to create and manage AI agents (voice/chat bots) for automating workflows including billing and payment experiences.

![System Architecture](docs/screenshots/architecture.png)
*Multi-tenant agent gateway with vendor abstraction and reliability features*

### Key Features

✅ **Multi-Tenant Core** - Complete tenant isolation with API key authentication
✅ **Vendor Abstraction** - Unified API across multiple AI providers (VendorA, VendorB)
✅ **Reliability Layer** - Automatic timeouts, retries with exponential backoff, and fallback providers
✅ **Usage Metering & Billing** - Accurate cost tracking per token with detailed analytics
✅ **Tool/Plugin Framework** - Extensible tool execution with audit logs (Invoice Lookup demo)
✅ **Observability** - Correlation IDs, structured JSON logging, provider call tracking
✅ **Idempotency** - Prevents double-charging on retried requests

## 🏗️ Architecture

```
┌─────────────┐
│   Tenants   │
│  (API Keys) │
└──────┬──────┘
       │
       ├─── Creates ───► ┌─────────┐
       │                 │ Agents  │
       │                 └────┬────┘
       │                      │
       └─────────────────────►│
                              ├─── primary: VendorA
                              ├─── fallback: VendorB
                              ├─── system_prompt
                              └─── enabled_tools

┌──────────────────────────────────────────────┐
│           Reliability Layer                   │
├──────────────────────────────────────────────┤
│  Timeout → Retry (exponential backoff) →     │
│  Fallback → Log all attempts                 │
└──────────────────────────────────────────────┘

┌──────────┐      ┌──────────┐
│ VendorA  │      │ VendorB  │
│ (10%     │      │ (HTTP    │
│ failure) │      │ 429)     │
└──────────┘      └──────────┘
```

## 📋 Prerequisites

- **Docker** & **Docker Compose** (for PostgreSQL + Redis)
- **Python 3.11+**
- **Node.js 18+** (for frontend)
- **Git**

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone/navigate to project
cd /Users/hardiksetia/Desktop/StitchFin

# Run complete setup script
./setup_and_run.sh
```

This script will:
1. ✅ Start PostgreSQL and Redis via Docker
2. ✅ Create Python virtual environment
3. ✅ Install all dependencies
4. ✅ Run database migrations
5. ✅ Seed 2 tenants with 3 agents each
6. ✅ Start FastAPI backend server

### Option 2: Manual Setup

#### 1. Start Database Services

```bash
docker-compose up -d
```

#### 2. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# OR
venv\\Scripts\\activate  # On Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env if needed (defaults work for local development)
```

#### 4. Run Database Migrations

```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

#### 5. Seed Demo Data

```bash
python scripts/seed.py
```

This creates:
- **2 Tenants**: TechCorp (software/SaaS) and HealthFirst (healthcare)
- **6 Agents**: 3 per tenant with different provider configurations
- **13 Invoices**: Company-specific invoice data for testing

**Save the API keys printed by the seed script!** You'll need them for API requests.

![Seed Script Output](docs/screenshots/seed-output.png)
*Seed script output showing generated API keys for TechCorp and HealthFirst tenants*

#### 6. Start Backend Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend is now running at: **http://localhost:8000**

## 📚 API Documentation

### Interactive API Docs

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

![Swagger API Documentation](docs/screenshots/swagger-ui.png)
*Interactive Swagger UI showing all available API endpoints with request/response schemas*

### Sample curl Commands

#### 1. Health Check

```bash
curl http://localhost:8000/health
```

#### 2. Create Tenant

```bash
curl -X POST http://localhost:8000/api/tenants \\
  -H "Content-Type: application/json" \\
  -d '{"name": "My Company"}'

# Response includes API key - save it!
```

#### 3. List Agents (requires API key)

```bash
curl -X GET http://localhost:8000/api/agents \\
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

#### 4. Create Session

```bash
curl -X POST http://localhost:8000/api/sessions \\
  -H "X-API-Key: YOUR_API_KEY_HERE" \\
  -H "Content-Type: application/json" \\
  -d '{
    "agent_id": "AGENT_UUID_FROM_LIST_AGENTS",
    "customer_id": "customer-123",
    "channel": "chat"
  }'

# Save the session_id from response
```

#### 5. Send Message (with idempotency)

```bash
curl -X POST http://localhost:8000/api/sessions/SESSION_UUID/messages \\
  -H "X-API-Key: YOUR_API_KEY_HERE" \\
  -H "Content-Type: application/json" \\
  -H "Idempotency-Key: unique-request-id-123" \\
  -d '{"content": "What is the status of invoice INV-001?"}'

# Response includes:
# - assistant response
# - tokens used (in/out)
# - cost in USD
# - latency
# - tools called
# - correlation ID
```

#### 6. Get Session Transcript

```bash
curl -X GET http://localhost:8000/api/sessions/SESSION_UUID \\
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

#### 7. Get Usage Analytics

```bash
curl -X GET "http://localhost:8000/api/analytics/usage?start_date=2025-12-01&end_date=2025-12-31" \\
  -H "X-API-Key: YOUR_API_KEY_HERE"

# Returns:
# - total sessions, messages, tokens, cost
# - breakdown by provider (VendorA vs VendorB)
```

#### 8. Get Top Agents by Cost

```bash
curl -X GET http://localhost:8000/api/analytics/top-agents?limit=5 \\
  -H "X-API-Key: YOUR_API_KEY_HERE"
```

## 🧪 Testing the Reliability Layer

### Test Retry Logic

Since VendorA has a 10% failure rate, sending multiple requests will trigger retries:

```bash
# Run this multiple times - you'll see retries in logs
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/sessions/SESSION_UUID/messages \\
    -H "X-API-Key: YOUR_API_KEY" \\
    -H "Content-Type: application/json" \\
    -d "{\"content\": \"Test message $i\"}"
  echo ""
done
```

Check `backend.log` to see:
- Retry attempts when VendorA fails (HTTP 500)
- Exponential backoff timing
- Fallback to VendorB when configured

### Test Fallback

Create an agent with VendorA primary and VendorB fallback. When VendorA fails after all retries, it automatically falls back to VendorB.

### Test Idempotency

```bash
# Send same request twice with same Idempotency-Key
IDEMPOTENCY_KEY="test-idempotency-$(date +%s)"

# First request
curl -X POST http://localhost:8000/api/sessions/SESSION_UUID/messages \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Test idempotency"}'

# Second request (immediate) - returns cached response
curl -X POST http://localhost:8000/api/sessions/SESSION_UUID/messages \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Test idempotency"}'

# Verify only ONE usage event was created (no double-charging)
```

## 🛠️ Tool Framework Demo

The Invoice Lookup tool is automatically available for agents with `enabled_tools: ["invoice_lookup"]`.

### Available Mock Invoices (Company-Specific)

**TechCorp Invoices:**
- **INV-TC-001**: $15,000.00, paid - Annual Enterprise License
- **INV-TC-002**: $8,500.00, pending - Professional Plan
- **INV-TC-003**: $3,200.00, overdue - Consulting Services
- **INV-TC-004**: $25,000.00, paid - Custom Development
- **INV-TC-005**: $12,000.00, pending - Premium Support
- **INV-TC-006**: $5,500.00, overdue - Integration Services

**HealthFirst Invoices:**
- **INV-HF-001**: $45,000.00, paid - Medical Equipment Supply
- **INV-HF-002**: $28,500.00, pending - Pharmaceutical Supplies
- **INV-HF-003**: $12,750.00, overdue - Diagnostic Equipment
- **INV-HF-004**: $67,000.00, paid - MRI Machine Installation
- **INV-HF-005**: $19,200.00, pending - Medical Software Licensing
- **INV-HF-006**: $8,900.00, overdue - Specialized Equipment Rental
- **INV-HF-007**: $34,000.00, paid - Emergency Response Equipment

*Note: Each tenant can only access their own invoices (tenant isolation enforced)*

### Test Tool Execution

```bash
# Using TechCorp API key
curl -X POST http://localhost:8000/api/sessions/SESSION_UUID/messages \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Look up invoice INV-TC-001"}'

# Response will include invoice details + tool execution logged to database
```

![Invoice Lookup Tool Execution](docs/screenshots/invoice-tool-demo.png)
*Chat session demonstrating invoice lookup tool execution with tenant-specific data isolation*

## 📊 Observability

### Correlation IDs

Every request gets a unique correlation ID that tracks the entire request lifecycle:

```bash
# Provide your own correlation ID
curl -X POST http://localhost:8000/api/sessions/SESSION_UUID/messages \\
  -H "X-API-Key: YOUR_API_KEY" \\
  -H "X-Correlation-ID: my-custom-correlation-id" \\
  -H "Content-Type: application/json" \\
  -d '{"content": "Hello"}'

# Correlation ID is returned in response headers and included in all logs
```

### Structured Logging

All logs are output as structured JSON:

```json
{
  "timestamp": "2025-12-27T10:30:45.123Z",
  "level": "INFO",
  "message": "VendorA: Success",
  "correlation_id": "abc-123",
  "tenant_id": "uuid-...",
  "provider": "vendorA",
  "latency_ms": 234
}
```

View logs:

```bash
# Follow live logs
tail -f backend.log

# Search by correlation ID
grep "correlation-id-here" backend.log

# View all vendor calls
grep "vendor_call" backend.log | jq
```


![Structured Logging Output]
*Sample structured JSON logs showing correlation IDs, provider calls, and retry attempts*

### Provider Call Tracking

All vendor call attempts are logged to the `provider_calls` table:

```sql
SELECT * FROM provider_calls
WHERE correlation_id = 'your-correlation-id'
ORDER BY created_at;

-- Shows:
-- - All retry attempts
-- - Fallback events
-- - Success/failure status
-- - Latency per attempt
```

![Provider Call Audit Trail]
*Database view of provider_calls table showing retry attempts, fallback events, and latency tracking*

## 💰 Cost Calculation

### Pricing

- **VendorA**: $0.002 per 1K tokens (input + output)
- **VendorB**: $0.003 per 1K tokens (input + output)

### Formula

```
cost_usd = ((tokens_in + tokens_out) / 1000) * price_per_1k_tokens
```

### Verify Billing

```bash
# Get usage analytics
curl -X GET http://localhost:8000/api/analytics/usage \\
  -H "X-API-Key: YOUR_API_KEY" | jq

# Check database directly
psql -U postgres -d vocalbridge -c "
  SELECT
    provider,
    SUM(tokens_in) as total_tokens_in,
    SUM(tokens_out) as total_tokens_out,
    SUM(cost_usd) as total_cost
  FROM usage_events
  GROUP BY provider;
"
```

![Usage Analytics Response](docs/screenshots/analytics-usage.png)
*Usage analytics API response showing token counts, costs, and provider breakdown*

## 🗄️ Database Schema

### Core Tables

- **tenants** - Tenant accounts with API keys
- **agents** - AI agent configurations
- **sessions** - Conversation sessions
- **messages** - Message transcripts
- **usage_events** - Billing events (cost per message)
- **provider_calls** - Provider call audit trail
- **tool_executions** - Tool call audit logs
- **idempotency_keys** - Idempotency cache

### Access Database

```bash
# Using Docker
docker exec -it vocalbridge-postgres psql -U postgres -d vocalbridge

# Example queries
\\dt  # List tables
SELECT * FROM tenants;
SELECT * FROM agents WHERE tenant_id = 'uuid';
SELECT * FROM usage_events ORDER BY created_at DESC LIMIT 10;
```

![Database Schema](docs/screenshots/database-schema.png)
*PostgreSQL database showing all 9 tables with relationships and key indexes*

## 🧪 Running Tests

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_vendors.py

# Run with coverage
pytest --cov=app tests/
```

![Test Execution Output](docs/screenshots/pytest-output.png)
*Pytest execution showing passing unit and integration tests with coverage report*

## 📁 Project Structure

```
VocalBridge/
├── backend/
│   ├── app/
│   │   ├── api/              # API endpoints
│   │   │   ├── tenants.py
│   │   │   ├── agents.py
│   │   │   ├── sessions.py
│   │   │   └── analytics.py
│   │   ├── models/           # Database models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── vendors/      # Vendor adapters
│   │   │   ├── reliability/  # Retry/fallback logic
│   │   │   ├── billing/      # Cost calculation
│   │   │   └── tools/        # Tool framework
│   │   ├── middleware/       # Auth, CORS, errors
│   │   ├── utils/            # Database, logging
│   │   └── main.py           # FastAPI app
│   ├── tests/                # Unit & integration tests
│   ├── scripts/              # Seed script
│   ├── alembic/              # Database migrations
│   └── requirements.txt
├── docker-compose.yml        # PostgreSQL + Redis
├── README.md                 # This file
└── ARCHITECTURE.md           # Detailed architecture docs
```

## 🔧 Configuration

Key environment variables (`.env`):

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/vocalbridge

# Pricing (per 1K tokens)
VENDOR_A_PRICE=0.002
VENDOR_B_PRICE=0.003

# Reliability
VENDOR_TIMEOUT_SECONDS=10
VENDOR_MAX_RETRIES=3
VENDOR_RETRY_MIN_WAIT=1
VENDOR_RETRY_MAX_WAIT=10
```

## 🚨 Troubleshooting

### Database Connection Errors

```bash
# Check if PostgreSQL is running
docker ps

# Restart database
docker-compose restart postgres

# Check logs
docker logs vocalbridge-postgres
```

### Migration Errors

```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
sleep 5
alembic upgrade head
python scripts/seed.py
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 PID

# Or change port
uvicorn app.main:app --port 8001
```

## 🎨 Frontend Dashboard

### Overview

A modern, production-ready React + TypeScript dashboard for managing AI agents, conducting live chat sessions, and analyzing usage metrics.

**Tech Stack:**
- React 18 + TypeScript
- Vite (build tool)
- React Router (navigation)
- React Query (API state management)
- TailwindCSS (styling)
- Recharts (analytics charts)
- Lucide React (icons)

### Features

✅ **API Key Authentication** - Secure login with persistent session storage
✅ **Agent Management** - Create, view, configure, and delete AI agents
✅ **Live Chat Interface** - Real-time messaging with cost/latency visibility
✅ **Voice Recording** - Browser-based audio capture with file upload support
✅ **Analytics Dashboard** - Usage statistics, cost breakdowns, provider comparison
✅ **Responsive Design** - Works on mobile, tablet, and desktop
✅ **Empty States & Onboarding** - Helpful guides for new users
✅ **Error Recovery** - Graceful error handling with retry mechanisms

### Quick Start

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Open browser to http://localhost:5173
```

**Prerequisites:**
- Node.js 18+
- Backend API running on http://localhost:8000
- API key from seed script (run `python backend/scripts/seed.py`)

See `frontend/README.md` for detailed documentation.

### Screenshots

**1. Login Page**
![Login Page](docs/screenshots/frontend-login.png)
*Clean API key authentication with helpful instructions and example keys*

**2. Agents Management**
![Agents Page](docs/screenshots/frontend-agents.png)
*Create and manage AI agents with provider configuration and tool enablement*

**3. Live Chat Interface**
*Real-time messaging with cost tracking, latency metrics, and provider visibility*

**4. Voice Recording**
![Voice Recording](docs/screenshots/frontend-voice.png)
*Browser-based audio recording with waveform visualization and upload support*

**5. Analytics Dashboard**
*Comprehensive usage statistics with charts for costs, tokens, and provider breakdown*



## 🎤 Voice Channel Integration (Bonus Feature)

### Overview

Complete voice interaction support with Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities, enabling users to communicate with AI agents using voice.

**Status: FULLY IMPLEMENTED**

### Architecture

```
User Audio → Frontend Recorder → Backend API → Whisper STT → Agent Processing → TTS → Audio Response
                                        ↓
                                  Audio Artifacts
                                   (Database)
```

### Features

✅ **Browser Audio Recording** - MediaRecorder API with real-time waveform
✅ **File Upload Support** - Accept pre-recorded audio files (.wav, .mp3, .m4a, .webm)
✅ **OpenAI Whisper STT** - High-accuracy speech-to-text transcription
✅ **OpenAI TTS** - Natural-sounding text-to-speech synthesis (6 voice options)
✅ **Audio Artifact Storage** - All audio files stored in PostgreSQL with metadata
✅ **Voice Session Management** - Dedicated "voice" channel with full transcript
✅ **Download Endpoints** - Retrieve any audio artifact by ID
✅ **Latency Tracking** - Measure STT, agent processing, and TTS latency separately

### Implementation Details

**Backend:**
- `backend/app/services/voice/stt.py` - Whisper STT service
- `backend/app/services/voice/tts.py` - OpenAI TTS service
- `backend/app/services/voice/handler.py` - Voice message orchestrator
- `backend/app/api/voice.py` - Voice API endpoints
- `backend/app/models/voice.py` - VoiceArtifact database model

**Frontend:**
- `frontend/src/components/VoiceRecorder.tsx` - Recording UI component
- `frontend/src/pages/Chat.tsx` - Integration with chat interface

### API Usage

```bash
# Create a voice session
curl -X POST http://localhost:8000/api/sessions \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGENT_UUID",
    "customer_id": "customer-123",
    "channel": "voice"
  }'

# Send voice message
curl -X POST http://localhost:8000/api/sessions/SESSION_UUID/voice/message \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "audio_file=@recording.wav"

# Download assistant's audio response (returns MP3 audio file)
curl -X GET http://localhost:8000/api/sessions/SESSION_UUID/voice/audio/MESSAGE_UUID \
  -H "X-API-Key: YOUR_API_KEY" \
  --output response.mp3

# Response: Binary MP3 audio file
# Content-Type: audio/mpeg
# The assistant's spoken response ready to play
```

![Audio Download API](docs/screenshots/audio-download-swagger.png)
*Swagger UI showing the audio download endpoint with response details*

### Screenshots

**Voice Recording Interface**
*Browser-based recording with timer and waveform visualization*

**Voice Session Transcript**
*Full conversation history with STT/TTS latency metrics 


**Audio Artifacts Table**
![Audio Artifacts](docs/screenshots/voice-artifacts-db.png)
*Database storage of all audio files with metadata and transcripts*

## 📈 Future Enhancements

The following features could be added to further expand the platform:

1. **Async Mode**
   - Job queue (Celery + Redis)
   - Background message processing
   - Completion webhooks for long-running tasks

2. **Real-time Features**
   - WebSocket support for streaming responses
   - Server-Sent Events (SSE) for live updates


3. **Additional Tools**
   - Payment processing (Stripe integration)
   - Calendar booking (Google Calendar API)
   - Email sending (SendGrid/Resend)
   - CRM integration (Salesforce, HubSpot)

4. **Enterprise Features**
   - Multi-user RBAC within tenants (admin, developer, viewer roles)
   - Cost forecasting & budget alerts
   - Rate limiting per tenant/agent
   - Audit logs with compliance exports
   - SSO integration (SAML, OAuth)



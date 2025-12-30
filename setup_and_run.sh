#!/bin/bash

# VocalBridge Ops - Complete Setup and Run Script
# This script sets up and runs the entire application

set -e  # Exit on error

echo "============================================================"
echo "VOCALBRIDGE OPS - COMPLETE SETUP"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required but not installed. Aborting." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Aborting." >&2; exit 1; }
echo -e "${GREEN}✓ All prerequisites met${NC}"
echo ""

# Step 2: Start Docker services
echo "🐳 Starting PostgreSQL and Redis..."
docker-compose up -d
echo -e "${GREEN}✓ Docker services started${NC}"
echo ""

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5
echo -e "${GREEN}✓ PostgreSQL ready${NC}"
echo ""

# Step 3: Setup backend
echo "🐍 Setting up Python backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"
echo ""

# Step 4: Create .env file if it doesn't exist
if [ ! -f "../.env" ]; then
    echo "Creating .env file..."
    cp ../.env.example ../.env
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${YELLOW}⚠ .env file already exists, skipping...${NC}"
fi
echo ""

# Step 5: Run database migrations
echo "🗄️  Running database migrations..."
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
    echo "Creating initial migration..."
    alembic revision --autogenerate -m "Initial migration"
fi
alembic upgrade head
echo -e "${GREEN}✓ Database migrations complete${NC}"
echo ""

# Step 6: Seed database
echo "🌱 Seeding database with demo data..."
python scripts/seed.py
echo -e "${GREEN}✓ Database seeded${NC}"
echo ""

# Step 7: Start backend server
echo "🚀 Starting FastAPI backend server..."
echo -e "${YELLOW}Backend will run on http://localhost:8000${NC}"
echo -e "${YELLOW}API docs available at http://localhost:8000/docs${NC}"
echo ""

# Run in background
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
echo ""

cd ..

echo "============================================================"
echo "✅ VOCALBRIDGE OPS BACKEND IS RUNNING!"
echo "============================================================"
echo ""
echo "📍 Backend API: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "📊 Health Check: http://localhost:8000/health"
echo ""
echo "🔑 Check backend.log for tenant API keys"
echo ""
echo "To stop the backend:"
echo "  kill $BACKEND_PID"
echo ""
echo "To view logs:"
echo "  tail -f backend.log"
echo ""
echo "============================================================"
echo "NEXT STEPS:"
echo "============================================================"
echo ""
echo "1. Test the API:"
echo "   curl http://localhost:8000/health"
echo ""
echo "2. Get tenant API keys from seed output above"
echo ""
echo "3. Create a session (replace API_KEY):"
echo "   curl -X POST http://localhost:8000/api/sessions \\"
echo "     -H \"X-API-Key: YOUR_API_KEY\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"agent_id\": \"AGENT_ID\", \"customer_id\": \"customer-123\"}'"
echo ""
echo "4. Frontend setup instructions in README.md"
echo ""

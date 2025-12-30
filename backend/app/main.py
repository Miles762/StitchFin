"""
VocalBridge Ops - Main FastAPI Application
Multi-Tenant Agent Gateway
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.middleware.correlation_id import CorrelationIDMiddleware
from app.middleware.error_handler import add_exception_handlers
from app.api import tenants, agents, sessions, analytics, voice
from app.utils.logger import setup_logging

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="VocalBridge Ops",
    description="Multi-Tenant Agent Gateway",
    version="1.0.0",
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

# Add exception handlers
add_exception_handlers(app)

# Include routers
app.include_router(tenants.router, prefix="/api/tenants", tags=["Tenants"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["Sessions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(voice.router, prefix="/api/sessions", tags=["Voice"])


@app.get("/")
async def root():
    return {
        "service": "VocalBridge Ops",
        "version": "1.0.0",
        "description": "Multi-Tenant Agent Gateway"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

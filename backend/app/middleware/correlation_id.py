"""
Correlation ID middleware - adds unique ID to each request
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import uuid
from app.utils.logger import set_correlation_id


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to generate and propagate correlation IDs
    """
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Set in context for logging
        set_correlation_id(correlation_id)

        # Store in request state for access in routes
        request.state.correlation_id = correlation_id

        # Process request
        response: Response = await call_next(request)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response

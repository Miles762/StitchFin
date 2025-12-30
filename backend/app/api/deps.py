"""
API dependencies
"""
from fastapi import Request
from typing import Optional


def get_correlation_id(request: Request) -> Optional[str]:
    """
    Get correlation ID from request state
    """
    return getattr(request.state, "correlation_id", None)


def get_idempotency_key(request: Request) -> Optional[str]:
    """
    Get idempotency key from request headers
    """
    return request.headers.get("Idempotency-Key") or request.headers.get("idempotency-key")

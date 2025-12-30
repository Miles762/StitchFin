"""
Structured logging utilities with correlation ID support
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id

        # Add extra fields from record
        if hasattr(record, 'tenant_id'):
            log_data["tenant_id"] = str(record.tenant_id)
        if hasattr(record, 'agent_id'):
            log_data["agent_id"] = str(record.agent_id)
        if hasattr(record, 'session_id'):
            log_data["session_id"] = str(record.session_id)
        if hasattr(record, 'provider'):
            log_data["provider"] = record.provider

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging():
    """
    Setup structured logging for the application
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove existing handlers
    logger.handlers = []

    # Create console handler with structured formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    """
    return logging.getLogger(name)


def set_correlation_id(correlation_id: str):
    """
    Set correlation ID for current context
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get correlation ID from current context
    """
    return correlation_id_var.get()


def log_event(logger: logging.Logger, event: str, level: str = "info", **kwargs):
    """
    Log a structured event with additional context
    """
    log_func = getattr(logger, level.lower())
    extra = {k: v for k, v in kwargs.items()}
    log_func(event, extra=extra)

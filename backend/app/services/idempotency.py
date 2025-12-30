"""
Idempotency key handling
"""
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
import json

from app.models.idempotency import IdempotencyKey
from app.utils.logger import get_logger

logger = get_logger(__name__)


def serialize_for_json(obj: Any) -> Any:
    """Convert objects to JSON-serializable format"""
    if isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    return obj


class IdempotencyService:
    """
    Handles idempotency key storage and retrieval
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def get_cached_response(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response for idempotency key

        Args:
            key: Idempotency key

        Returns:
            Cached response or None if not found/expired
        """
        record = self.db.query(IdempotencyKey).filter(
            IdempotencyKey.key == key,
            IdempotencyKey.tenant_id == self.tenant_id,
            IdempotencyKey.expires_at > datetime.utcnow()
        ).first()

        if record:
            logger.info(
                f"Idempotency key hit: {key}",
                extra={"tenant_id": str(self.tenant_id)}
            )
            return record.response

        return None

    def cache_response(self, key: str, response: Dict[str, Any], ttl_hours: int = 24):
        """
        Cache response for idempotency key

        Args:
            key: Idempotency key
            response: Response to cache
            ttl_hours: Time to live in hours (default 24)
        """
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)

        # Serialize response to ensure JSON compatibility
        serialized_response = serialize_for_json(response)

        idempotency_key = IdempotencyKey(
            key=key,
            tenant_id=self.tenant_id,
            response=serialized_response,
            created_at=datetime.utcnow(),
            expires_at=expires_at
        )

        self.db.merge(idempotency_key)  # Use merge to handle duplicates
        self.db.commit()

        logger.info(
            f"Idempotency key cached: {key}",
            extra={"tenant_id": str(self.tenant_id), "expires_at": expires_at.isoformat()}
        )

    def cleanup_expired(self):
        """Clean up expired idempotency keys"""
        deleted = self.db.query(IdempotencyKey).filter(
            IdempotencyKey.expires_at < datetime.utcnow()
        ).delete()

        self.db.commit()

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired idempotency keys")

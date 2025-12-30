"""
Resilient vendor caller with timeout, retry, and fallback
"""
import asyncio
import time
from typing import Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
from sqlalchemy.orm import Session

from app.services.vendors.base import VendorAdapter, VendorRequest, NormalizedResponse
from app.services.vendors.factory import get_vendor_adapter
from app.models.usage import ProviderCall
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VendorCallTimeout(Exception):
    """Raised when vendor call times out"""
    pass


class AllVendorsFailed(Exception):
    """Raised when both primary and fallback vendors fail"""
    def __init__(self, primary_error: str, fallback_error: Optional[str] = None):
        self.primary_error = primary_error
        self.fallback_error = fallback_error
        message = f"Primary vendor failed: {primary_error}"
        if fallback_error:
            message += f". Fallback vendor also failed: {fallback_error}"
        super().__init__(message)


class ResilientVendorCaller:
    """
    Handles vendor calls with timeout, retry, and fallback logic
    """

    def __init__(
        self,
        tenant_id: str,
        session_id: str,
        correlation_id: str,
        db: Session
    ):
        self.tenant_id = tenant_id
        self.session_id = session_id
        self.correlation_id = correlation_id
        self.db = db
        self.timeout_seconds = settings.VENDOR_TIMEOUT_SECONDS
        self.max_retries = settings.VENDOR_MAX_RETRIES

    def _log_provider_call(
        self,
        provider: str,
        attempt_number: int,
        status: str,
        http_status: Optional[int] = None,
        latency_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Log provider call event to database"""
        provider_call = ProviderCall(
            tenant_id=self.tenant_id,
            session_id=self.session_id,
            correlation_id=self.correlation_id,
            provider=provider,
            attempt_number=attempt_number,
            status=status,
            http_status=http_status,
            latency_ms=latency_ms,
            error_message=error_message
        )
        self.db.add(provider_call)
        self.db.commit()

        logger.info(
            f"Provider call logged",
            extra={
                "provider": provider,
                "status": status,
                "attempt": attempt_number,
                "correlation_id": self.correlation_id
            }
        )

    async def _call_with_timeout(
        self,
        vendor: VendorAdapter,
        request: VendorRequest
    ) -> NormalizedResponse:
        """Call vendor with timeout"""
        try:
            response = await asyncio.wait_for(
                vendor.call(request),
                timeout=self.timeout_seconds
            )
            return response
        except asyncio.TimeoutError:
            raise VendorCallTimeout(f"Vendor call timed out after {self.timeout_seconds}s")

    async def _call_with_retry(
        self,
        vendor: VendorAdapter,
        request: VendorRequest,
        attempt_offset: int = 0
    ) -> NormalizedResponse:
        """Call vendor with exponential backoff retry"""

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(
                multiplier=1,
                min=settings.VENDOR_RETRY_MIN_WAIT,
                max=settings.VENDOR_RETRY_MAX_WAIT
            ),
            retry=retry_if_exception_type((
                VendorCallTimeout,
                Exception  # Catch all vendor exceptions
            )),
            reraise=True
        )
        async def _retry_call(attempt_number: int):
            start_time = time.time()
            try:
                logger.info(
                    f"Calling {vendor.name} (attempt {attempt_number})",
                    extra={"provider": vendor.name, "correlation_id": self.correlation_id}
                )

                response = await self._call_with_timeout(vendor, request)
                latency_ms = int((time.time() - start_time) * 1000)

                # Log success
                self._log_provider_call(
                    provider=vendor.name,
                    attempt_number=attempt_number + attempt_offset,
                    status="success",
                    http_status=200,
                    latency_ms=latency_ms
                )

                return response

            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                http_status = getattr(e, 'status_code', None) or 500
                error_msg = str(e)

                # Log retry
                self._log_provider_call(
                    provider=vendor.name,
                    attempt_number=attempt_number + attempt_offset,
                    status="retry",
                    http_status=http_status,
                    latency_ms=latency_ms,
                    error_message=error_msg
                )

                logger.warning(
                    f"{vendor.name} failed (attempt {attempt_number}): {error_msg}",
                    extra={"provider": vendor.name, "correlation_id": self.correlation_id}
                )

                raise

        # Try with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                return await _retry_call(attempt)
            except RetryError as e:
                if attempt == self.max_retries:
                    # All retries exhausted
                    raise e.last_attempt.exception()

    async def call_with_fallback(
        self,
        primary_provider: str,
        fallback_provider: Optional[str],
        request: VendorRequest
    ) -> NormalizedResponse:
        """
        Call primary vendor, with fallback if it fails

        Args:
            primary_provider: Primary vendor name
            fallback_provider: Fallback vendor name (optional)
            request: Request to send

        Returns:
            Normalized response

        Raises:
            AllVendorsFailed: If both primary and fallback fail
        """
        primary_vendor = get_vendor_adapter(primary_provider)
        primary_error = None

        # Try primary vendor
        try:
            logger.info(
                f"Trying primary vendor: {primary_provider}",
                extra={"provider": primary_provider, "correlation_id": self.correlation_id}
            )
            return await self._call_with_retry(primary_vendor, request)

        except Exception as e:
            primary_error = str(e)
            logger.error(
                f"Primary vendor {primary_provider} failed: {primary_error}",
                extra={"provider": primary_provider, "correlation_id": self.correlation_id}
            )

            # Log failure
            self._log_provider_call(
                provider=primary_provider,
                attempt_number=self.max_retries,
                status="error",
                error_message=primary_error
            )

        # Try fallback if configured
        if not fallback_provider:
            raise AllVendorsFailed(primary_error)

        logger.info(
            f"Falling back to: {fallback_provider}",
            extra={"provider": fallback_provider, "correlation_id": self.correlation_id}
        )

        # Log fallback attempt
        self._log_provider_call(
            provider=fallback_provider,
            attempt_number=1,
            status="fallback"
        )

        fallback_vendor = get_vendor_adapter(fallback_provider)
        fallback_error = None

        try:
            return await self._call_with_retry(
                fallback_vendor,
                request,
                attempt_offset=self.max_retries  # Continue attempt numbering
            )

        except Exception as e:
            fallback_error = str(e)
            logger.error(
                f"Fallback vendor {fallback_provider} failed: {fallback_error}",
                extra={"provider": fallback_provider, "correlation_id": self.correlation_id}
            )

            # Log fallback failure
            self._log_provider_call(
                provider=fallback_provider,
                attempt_number=self.max_retries,
                status="error",
                error_message=fallback_error
            )

        raise AllVendorsFailed(primary_error, fallback_error)

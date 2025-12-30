"""
Base vendor adapter interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from pydantic import BaseModel


class VendorRequest(BaseModel):
    """Normalized request to vendor"""
    system_prompt: str
    user_message: str
    conversation_history: list = []


class NormalizedResponse(BaseModel):
    """Normalized response from vendor"""
    text: str
    tokens_in: int
    tokens_out: int
    latency_ms: int


class VendorAdapter(ABC):
    """
    Abstract base class for all vendor adapters
    Implements Strategy pattern for different AI providers
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Vendor identifier"""
        pass

    @abstractmethod
    async def send_message(self, request: VendorRequest) -> Dict[str, Any]:
        """
        Send message to vendor and get raw response

        Args:
            request: Normalized vendor request

        Returns:
            Raw vendor response (vendor-specific format)
        """
        pass

    @abstractmethod
    def normalize_response(self, raw_response: Dict[str, Any]) -> NormalizedResponse:
        """
        Normalize vendor-specific response to common format

        Args:
            raw_response: Raw response from vendor

        Returns:
            Normalized response
        """
        pass

    async def call(self, request: VendorRequest) -> NormalizedResponse:
        """
        High-level call that handles send and normalization

        Args:
            request: Normalized vendor request

        Returns:
            Normalized response
        """
        raw_response = await self.send_message(request)
        return self.normalize_response(raw_response)

"""
VendorA implementation - OpenAI GPT-4o-mini
"""
import time
from typing import Dict, Any
from openai import AsyncOpenAI
from app.services.vendors.base import VendorAdapter, VendorRequest, NormalizedResponse
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VendorA(VendorAdapter):
    """
    VendorA - OpenAI GPT-4o-mini implementation
    """

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured in settings")
        self.client = AsyncOpenAI(api_key=api_key)

    @property
    def name(self) -> str:
        return "vendorA"

    async def send_message(self, request: VendorRequest) -> Dict[str, Any]:
        """
        Call OpenAI GPT-4o-mini API
        """
        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # ChatGPT-4o-mini
                messages=[
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )

            actual_latency = int((time.time() - start_time) * 1000)

            result = {
                "outputText": response.choices[0].message.content,
                "tokensIn": response.usage.prompt_tokens,
                "tokensOut": response.usage.completion_tokens,
                "latencyMs": actual_latency
            }

            logger.info(f"VendorA (GPT-4o-mini): Success - latency={actual_latency}ms, tokens={result['tokensIn']}/{result['tokensOut']}")
            return result

        except Exception as e:
            logger.error(f"VendorA (GPT-4o-mini): Error - {str(e)}")
            raise

    def normalize_response(self, raw_response: Dict[str, Any]) -> NormalizedResponse:
        """
        Normalize VendorA response format
        """
        return NormalizedResponse(
            text=raw_response["outputText"],
            tokens_in=raw_response["tokensIn"],
            tokens_out=raw_response["tokensOut"],
            latency_ms=raw_response["latencyMs"]
        )

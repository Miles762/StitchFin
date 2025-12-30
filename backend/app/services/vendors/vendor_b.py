"""
VendorB implementation - Google Gemini 2.5 Flash
"""
import time
from typing import Dict, Any
import google.generativeai as genai
from app.services.vendors.base import VendorAdapter, VendorRequest, NormalizedResponse
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class VendorB(VendorAdapter):
    """
    VendorB - Google Gemini 2.5 Flash implementation
    """

    def __init__(self):
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not configured in settings")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    @property
    def name(self) -> str:
        return "vendorB"

    async def send_message(self, request: VendorRequest) -> Dict[str, Any]:
        """
        Call Google Gemini 2.0 Flash API
        """
        start_time = time.time()

        try:
            # Combine system prompt and user message
            full_prompt = f"{request.system_prompt}\n\nUser: {request.user_message}"

            response = await self.model.generate_content_async(
                full_prompt,
                generation_config={
                    'temperature': 0.7,
                    'max_output_tokens': 500,
                }
            )

            actual_latency = int((time.time() - start_time) * 1000)

            # Extract token counts
            input_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
            output_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0

            result = {
                "choices": [
                    {
                        "message": {
                            "content": response.text
                        }
                    }
                ],
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                },
                "latency_ms": actual_latency
            }

            logger.info(f"VendorB (Gemini 2.0 Flash): Success - latency={actual_latency}ms, tokens={input_tokens}/{output_tokens}")
            return result

        except Exception as e:
            logger.error(f"VendorB (Gemini 2.0 Flash): Error - {str(e)}")
            raise

    def normalize_response(self, raw_response: Dict[str, Any]) -> NormalizedResponse:
        """
        Normalize VendorB response format
        """
        return NormalizedResponse(
            text=raw_response["choices"][0]["message"]["content"],
            tokens_in=raw_response["usage"]["input_tokens"],
            tokens_out=raw_response["usage"]["output_tokens"],
            latency_ms=raw_response.get("latency_ms", 0)
        )

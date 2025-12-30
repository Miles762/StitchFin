"""
Application configuration
"""
from pydantic_settings import BaseSettings
from typing import List
from decimal import Decimal


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/vocalbridge"
    TEST_DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/vocalbridge_test"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Application
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Pricing (per 1K tokens)
    VENDOR_A_PRICE: Decimal = Decimal("0.002")
    VENDOR_B_PRICE: Decimal = Decimal("0.003")

    # Reliability
    VENDOR_TIMEOUT_SECONDS: int = 10
    VENDOR_MAX_RETRIES: int = 3
    VENDOR_RETRY_MIN_WAIT: int = 1
    VENDOR_RETRY_MAX_WAIT: int = 10

    # Voice
    MAX_AUDIO_SIZE_MB: int = 10
    AUDIO_STORAGE_PATH: str = "backend/app/audio_artifacts"

    # AI Provider API Keys
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Pricing table
PRICING = {
    "vendorA": {
        "input_tokens": Decimal("0.002"),   # $0.002 per 1K tokens
        "output_tokens": Decimal("0.002"),
    },
    "vendorB": {
        "input_tokens": Decimal("0.003"),   # $0.003 per 1K tokens
        "output_tokens": Decimal("0.003"),
    },
}


settings = Settings()

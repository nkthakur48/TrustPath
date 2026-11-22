from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "TrustPath API"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # OpenRouter (all LLM calls). Empty key = LLM step skipped, rules only.
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_TIMEOUT_SECONDS: float = 15
    # Without a cap OpenRouter reserves the model's full output limit, which low-credit keys can't afford.
    LLM_MAX_TOKENS: int = 1200

    # Gmail (read-only OAuth). Empty client id = Gmail feature disabled.
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/gmail/callback"
    FRONTEND_URL: str = "http://localhost:5173"

    # Origins allowed to call the API from a browser (the future frontend).
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://localhost:5500"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

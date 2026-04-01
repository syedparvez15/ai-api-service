"""
Application configuration loaded from environment variables.
Uses pydantic-settings for type-safe config management.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    app_name: str = "AI API Service"
    app_env: str = "development"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # OpenAI
    openai_api_key: str = "mock-key"
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 1024
    openai_temperature: float = 0.7

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 300

    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 500

    # Security
    api_key_header: str = "X-API-Key"
    allowed_api_keys: str = "dev-key-001,dev-key-002"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def allowed_keys_list(self) -> list[str]:
        return [k.strip() for k in self.allowed_api_keys.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once at startup."""
    return Settings()

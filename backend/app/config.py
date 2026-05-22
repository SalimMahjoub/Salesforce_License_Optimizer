"""Application configuration using Pydantic Settings (Pydantic v2 style)."""
from functools import lru_cache
from typing import List, Optional

from cryptography.fernet import Fernet
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "salesforce-license-optimizer"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str
    database_pool_size: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Data provider: "demo" (in-memory) or "salesforce" (live OAuth)
    data_provider: str = "demo"

    # Salesforce OAuth
    sf_client_id: str
    sf_client_secret: str
    sf_redirect_uri: str

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4"

    # Notifications
    slack_webhook_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # Security
    secret_key: str = Field(..., min_length=32)
    # Persistent Fernet key for token encryption. If not provided, a key is
    # generated at startup — fine for dev, but tokens will not survive restart.
    # Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: Optional[str] = None
    cors_origins: List[str] = ["http://localhost:3000"]

    # Observability
    sentry_dsn: Optional[str] = None
    json_logs: bool = False

    @field_validator("encryption_key")
    @classmethod
    def _validate_fernet(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "":
            return None
        try:
            Fernet(v.encode())
        except Exception as exc:
            raise ValueError(
                "ENCRYPTION_KEY must be a valid 44-char base64 Fernet key"
            ) from exc
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


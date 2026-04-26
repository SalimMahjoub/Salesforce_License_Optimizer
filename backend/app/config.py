"""Application configuration using Pydantic Settings"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
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
    secret_key: str
    cors_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


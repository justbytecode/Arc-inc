"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://csvuser:csvpassword@localhost:5432/csvimport"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    AUTH_TOKEN: str = "dev-auth-token"  # Simple token auth for demo
    
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Import settings
    BATCH_SIZE: int = 1000  # Rows per batch for upsert
    MAX_ERROR_SAMPLES: int = 100  # Store first N errors
    
    # Webhook settings
    WEBHOOK_TIMEOUT: int = 30  # Seconds
    WEBHOOK_MAX_RETRIES: int = 5
    WEBHOOK_RETRY_DELAYS: list = [60, 300, 900, 3600, 7200]  # Exponential backoff in seconds
    
    # File upload
    MAX_UPLOAD_SIZE: int = 500 * 1024 * 1024  # 500MB
    UPLOAD_DIR: str = "/app/uploads"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

"""
Configuration settings for Mission Control v2
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App
    APP_NAME: str = "Mission Control v2"
    DEBUG: bool = False

    # MongoDB
    MONGODB_URL: str = "mongodb://admin:password@mongodb:27017"
    MONGODB_DB: str = "mission_control"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # JWT (Phase 2)
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 15

    # Platform
    PLATFORM_PATH: str = "/app/platform"

    # CORS
    CORS_ORIGINS: list = ["*"]  # Allow all origins (internal tool)

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

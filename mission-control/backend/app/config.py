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
    MONGODB_URL: str = "mongodb://mongodb:27017"
    MONGODB_DB: str = "mission_control"

    # Redis
    REDIS_URL: str = "redis://redis:6379"

    # JWT & Auth
    JWT_SECRET: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24 * 7  # 7 days
    AUTH_PASSWORD: str = "mission2026"  # Simple password for login

    # Platform
    PLATFORM_PATH: str = "/app/platform"

    # Gitea
    GITEA_URL: str = "http://192.168.80.203:3000"
    GITEA_TOKEN: str = "e5403eda27854b7cb7474832338a81eac26e92d2"
    GITEA_USER: str = "wit"

    # CORS
    CORS_ORIGINS: list = ["*"]  # Allow all origins (internal tool)

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

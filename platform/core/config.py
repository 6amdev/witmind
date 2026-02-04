"""
6amdev Server - Configuration Management
Centralized configuration loader from .env file
"""
import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Find project root and load .env
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


@dataclass
class LLMConfig:
    """LLM Provider Configuration"""
    # Claude
    claude_api_key: str = field(default_factory=lambda: os.getenv("CLAUDE_API_KEY", ""))
    claude_default_model: str = field(default_factory=lambda: os.getenv("CLAUDE_DEFAULT_MODEL", "claude-sonnet-4-20250514"))

    # OpenRouter
    openrouter_api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    openrouter_default_model: str = field(default_factory=lambda: os.getenv("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-3.5-sonnet"))

    # Ollama
    ollama_enabled: bool = field(default_factory=lambda: os.getenv("OLLAMA_ENABLED", "true").lower() == "true")
    ollama_url: str = field(default_factory=lambda: os.getenv("OLLAMA_URL", "http://localhost:11434"))
    ollama_default_model: str = field(default_factory=lambda: os.getenv("OLLAMA_DEFAULT_MODEL", "qwen2.5-coder:14b"))

    # Strategy
    strategy: str = field(default_factory=lambda: os.getenv("LLM_STRATEGY", "auto"))


@dataclass
class StorageConfig:
    """Storage Configuration"""
    # Base paths
    data_path: Path = field(default_factory=lambda: Path(os.getenv("DATA_PATH", "/mnt/data")))
    fast_storage_path: Path = field(default_factory=lambda: Path(os.getenv("FAST_STORAGE_PATH", str(PROJECT_ROOT))))

    # Specific paths
    docker_storage_path: Path = field(default_factory=lambda: Path(os.getenv("DOCKER_STORAGE_PATH", "/mnt/data/docker-storage")))
    ai_models_path: Path = field(default_factory=lambda: Path(os.getenv("AI_MODELS_PATH", "/mnt/data/ai-models")))
    backup_path: Path = field(default_factory=lambda: Path(os.getenv("BACKUP_PATH", "/mnt/data/backups")))
    projects_path: Path = field(default_factory=lambda: Path(os.getenv("PROJECTS_PATH", "/mnt/data/projects")))
    log_path: Path = field(default_factory=lambda: Path(os.getenv("LOG_PATH", "/var/log/6amdev")))

    def ensure_directories(self):
        """Create storage directories if they don't exist"""
        for path in [self.data_path, self.ai_models_path, self.backup_path, self.projects_path]:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                pass  # May need sudo


@dataclass
class DatabaseConfig:
    """Database Configuration"""
    # MongoDB
    mongodb_url: str = field(default_factory=lambda: os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    mongodb_database: str = field(default_factory=lambda: os.getenv("MONGODB_DATABASE", "6amdev"))

    # Redis
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    redis_password: str = field(default_factory=lambda: os.getenv("REDIS_PASSWORD", ""))


@dataclass
class ServerConfig:
    """Server Configuration"""
    # Deployment
    profile: str = field(default_factory=lambda: os.getenv("DEPLOYMENT_PROFILE", "local"))
    server_name: str = field(default_factory=lambda: os.getenv("SERVER_NAME", "6amdev-server"))
    server_ip: str = field(default_factory=lambda: os.getenv("SERVER_IP", "localhost"))

    # Ports
    mission_control_port: int = field(default_factory=lambda: int(os.getenv("MISSION_CONTROL_PORT", "4001")))
    todo_app_port: int = field(default_factory=lambda: int(os.getenv("TODO_APP_PORT", "4002")))
    api_port: int = field(default_factory=lambda: int(os.getenv("API_PORT", "8000")))

    # URLs
    external_url: str = field(default_factory=lambda: os.getenv("EXTERNAL_URL", "http://localhost"))

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "info"))


@dataclass
class Config:
    """Main Configuration Container"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    @property
    def is_local(self) -> bool:
        return self.server.profile == "local"

    @property
    def is_cloud(self) -> bool:
        return self.server.profile == "cloud"

    @property
    def is_dev(self) -> bool:
        return self.server.profile == "dev"


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get configuration singleton"""
    global _config
    if _config is None:
        _config = Config()
    return _config


# Convenience accessors
def get_llm_config() -> LLMConfig:
    return get_config().llm


def get_storage_config() -> StorageConfig:
    return get_config().storage


def get_database_config() -> DatabaseConfig:
    return get_config().database


def get_server_config() -> ServerConfig:
    return get_config().server


# Quick access to common values
def get_claude_api_key() -> str:
    return get_llm_config().claude_api_key


def get_mongodb_url() -> str:
    return get_database_config().mongodb_url


def get_redis_url() -> str:
    return get_database_config().redis_url


def get_data_path() -> Path:
    return get_storage_config().data_path


if __name__ == "__main__":
    # Test configuration
    config = get_config()
    print(f"Profile: {config.server.profile}")
    print(f"Data Path: {config.storage.data_path}")
    print(f"LLM Strategy: {config.llm.strategy}")
    print(f"Ollama Enabled: {config.llm.ollama_enabled}")
    print(f"MongoDB: {config.database.mongodb_url}")

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Application
    APP_NAME: str = "AgentOps AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    APP_SECRET_KEY: str = "agentops-super-secure-production-ready-secret-key-32b"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Networking
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./agentops.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False

    # Qdrant Vector Store
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_STORAGE_PATH: str = "./qdrant_data"
    QDRANT_COLLECTION_NAME: str = "agentops_knowledge_base"

    # LLM Settings
    OPENAI_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gpt-4o"
    OPENAI_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    MAX_INVESTIGATION_STEPS: int = 15
    MAX_RETRY_LIMIT: int = 3
    TOKEN_BUDGET_PER_INVESTIGATION: int = 50000

    # Sandbox / Execution
    SANDBOX_EXECUTION_TIMEOUT_SECONDS: int = 45
    SANDBOX_MAX_MEMORY_MB: int = 512
    SANDBOX_MAX_CPU_PERCENT: int = 80
    SANDBOX_DOCKER_IMAGE: str = "python:3.12-slim"
    ENABLE_DOCKER_SANDBOX: bool = False

    # GitHub
    GITHUB_TOKEN: str = ""
    GITHUB_ORG: str = ""

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()

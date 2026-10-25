from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./compute_csi.db"

    # Temporal
    TEMPORAL_ADDRESS: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "compute-csi-queue"

    # Prometheus
    PROMETHEUS_URL: str = "http://localhost:9090"

    # Kepler
    KEPLER_ENABLED: bool = False

    # Gemma
    GEMMA_ENDPOINT: str = ""
    GEMMA_API_KEY: str = ""
    GEMMA_MODEL: str = "gemma2-2b-it"

    # JarvisLabs
    JARVISLABS_API_KEY: str = ""
    JARVISLABS_INSTANCE_URL: str = ""

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()

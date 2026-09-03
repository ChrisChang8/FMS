from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    app_name: str = "FMS Market Data Simulator"
    environment: str = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    database_url: str | None = None
    database_pool_min_size: int = 1
    database_pool_max_size: int = 5
    persistence_queue_capacity: int = 128
    persistence_high_water_mark: int = 96
    persistence_low_water_mark: int = 32
    persistence_retry_limit: int = 5
    persistence_retry_base_seconds: float = 0.1
    persistence_shutdown_timeout_seconds: float = 10.0
    history_page_limit: int = 500
    replay_min_speed: float = 0.1
    replay_max_speed: float = 20.0

    model_config = SettingsConfigDict(env_prefix="FMS_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

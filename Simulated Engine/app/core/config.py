from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    app_name: str = "FMS Market Data Simulator"
    environment: str = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(env_prefix="FMS_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

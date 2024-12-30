"""Application settings."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    github_token: Optional[str] = None
    max_workers: Optional[int] = None

    model_config = SettingsConfigDict(env_file=".env")


SETTINGS = Settings()

"""Application settings."""

import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    github_token: Optional[str] = None
    max_workers: Optional[int] = os.cpu_count() or 1

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


SETTINGS = Settings()

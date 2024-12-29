from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    better_exceptions: int = 0
    github_token: str | None = None
    max_workers: int | None = None

    model_config = SettingsConfigDict(env_file=".env")


SETTINGS = Settings()

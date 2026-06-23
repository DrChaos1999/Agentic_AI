from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "Bangla Order Agent"
    app_version: str = "1.0.0"
    environment: str = "development"
    database_url: str = "sqlite:///./bangla_orders.db"
    duplicate_window_hours: int = Field(default=24, ge=1, le=720)
    openai_api_key: str | None = None
    openai_model: str | None = None
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key and self.openai_model)

    def ensure_sqlite_parent(self) -> None:
        prefix = "sqlite:///"
        if self.database_url.startswith(prefix):
            raw_path = self.database_url.removeprefix(prefix)
            if raw_path != ":memory:":
                Path(raw_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_sqlite_parent()
    return settings

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "FactoryLens AI"
    environment: Literal["development", "test", "production"] = "development"
    api_prefix: str = "/api/v1"
    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "sqlite:///./factorylens.db"
    upload_dir: Path = Path("data/uploads")
    max_upload_mb: int = 10

    model_path: Path = Path("models/factorylens_resnet18.pt")
    image_size: int = 224
    device: str = "auto"
    demo_mode: bool = True

    faiss_index_path: Path = Path("artifacts/faiss/image.index")
    faiss_metadata_path: Path = Path("artifacts/faiss/image_metadata.json")
    faiss_vectors_path: Path = Path("artifacts/faiss/image_vectors.npy")
    faiss_index_type: Literal["flat", "hnsw", "ivf"] = "flat"

    manual_path: Path = Path("data/manual/maintenance_manual.md")
    manual_index_path: Path = Path("artifacts/faiss/manual.index")
    manual_metadata_path: Path = Path("artifacts/faiss/manual_metadata.json")

    top_k: int = 5
    confidence_threshold: float = 0.55

    mlflow_tracking_uri: str = "sqlite:///./mlflow.db"
    mlflow_experiment_name: str = "factorylens-defect-classification"
    mlflow_registered_model_name: str = "FactoryLensDefectClassifier"

    enable_llm: bool = False
    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-5.4-mini"

    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    @property
    def parsed_cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    def ensure_directories(self) -> None:
        for path in (
            self.upload_dir,
            self.model_path.parent,
            self.faiss_index_path.parent,
            self.manual_index_path.parent,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

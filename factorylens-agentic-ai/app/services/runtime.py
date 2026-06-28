from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.retrieval.faiss_store import FaissVectorStore
from app.retrieval.manual_store import ManualFaissStore
from app.vision.service import VisionService


@dataclass(slots=True)
class RuntimeServices:
    settings: Settings
    vision: VisionService
    image_store: FaissVectorStore
    manual_store: ManualFaissStore


def create_runtime(settings: Settings) -> RuntimeServices:
    image_store = FaissVectorStore.load(
        settings.faiss_index_path,
        settings.faiss_metadata_path,
        settings.faiss_vectors_path,
    )
    if image_store.dimension is None:
        image_store.index_type = settings.faiss_index_type
    manual_store = ManualFaissStore.load_or_build(
        settings.manual_path,
        settings.manual_index_path,
        settings.manual_metadata_path,
    )
    return RuntimeServices(
        settings=settings,
        vision=VisionService(settings),
        image_store=image_store,
        manual_store=manual_store,
    )

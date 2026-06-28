from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from threading import RLock
from typing import Any

import numpy as np

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover - handled by numpy fallback
    faiss = None


def normalize_rows(vectors: np.ndarray) -> np.ndarray:
    vectors = np.asarray(vectors, dtype="float32")
    if vectors.ndim == 1:
        vectors = vectors.reshape(1, -1)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vectors / norms


class FaissVectorStore:
    """Thread-safe FAISS store with a NumPy fallback for development and tests."""

    def __init__(self, index_type: str = "flat") -> None:
        self.index_type = index_type
        self.dimension: int | None = None
        self.index: Any | None = None
        self.metadata: list[dict[str, Any]] = []
        self._numpy_vectors = np.empty((0, 0), dtype="float32")
        self._lock = RLock()

    @property
    def backend(self) -> str:
        return "faiss" if faiss is not None else "numpy-fallback"

    @property
    def size(self) -> int:
        if self.index is not None:
            return int(self.index.ntotal)
        return int(len(self._numpy_vectors))

    @property
    def ready(self) -> bool:
        return self.dimension is not None and self.size > 0

    def _create_index(self, dimension: int, expected_size: int) -> Any:
        if faiss is None:
            return None
        if self.index_type == "hnsw":
            index = faiss.IndexHNSWFlat(dimension, 32, faiss.METRIC_INNER_PRODUCT)
            index.hnsw.efConstruction = 80
            index.hnsw.efSearch = 64
            return index
        if self.index_type == "ivf":
            nlist = max(1, min(128, int(np.sqrt(max(expected_size, 1)))))
            quantizer = faiss.IndexFlatIP(dimension)
            return faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
        return faiss.IndexFlatIP(dimension)

    def build(self, vectors: np.ndarray, metadata: Iterable[dict[str, Any]]) -> None:
        vectors = normalize_rows(vectors)
        items = list(metadata)
        if vectors.shape[0] != len(items):
            raise ValueError("The number of vectors and metadata records must match.")
        if not items:
            raise ValueError("Cannot build an empty vector index.")
        with self._lock:
            self.dimension = int(vectors.shape[1])
            self.metadata = items
            self.index = self._create_index(self.dimension, len(items))
            if self.index is not None:
                if hasattr(self.index, "is_trained") and not self.index.is_trained:
                    self.index.train(vectors)
                self.index.add(vectors)
                self._numpy_vectors = np.empty((0, self.dimension), dtype="float32")
            else:
                self._numpy_vectors = vectors.copy()

    def add(self, vectors: np.ndarray, metadata: Iterable[dict[str, Any]]) -> None:
        vectors = normalize_rows(vectors)
        items = list(metadata)
        if len(items) != vectors.shape[0]:
            raise ValueError("The number of vectors and metadata records must match.")
        with self._lock:
            if self.dimension is None:
                self.build(vectors, items)
                return
            if vectors.shape[1] != self.dimension:
                raise ValueError(f"Expected dimension {self.dimension}, received {vectors.shape[1]}.")
            if self.index is not None:
                self.index.add(vectors)
            else:
                self._numpy_vectors = np.vstack([self._numpy_vectors, vectors])
            self.metadata.extend(items)

    def search(self, query: np.ndarray, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.ready:
            return []
        query = normalize_rows(query)
        if query.shape[1] != self.dimension:
            raise ValueError(f"Expected query dimension {self.dimension}, received {query.shape[1]}.")
        top_k = min(max(int(top_k), 1), self.size)
        with self._lock:
            if self.index is not None:
                scores, indices = self.index.search(query, top_k)
                pairs = zip(scores[0].tolist(), indices[0].tolist(), strict=False)
            else:
                scores = self._numpy_vectors @ query[0]
                indices = np.argsort(-scores)[:top_k]
                pairs = ((float(scores[i]), int(i)) for i in indices)
            results: list[dict[str, Any]] = []
            for score, idx in pairs:
                if idx < 0 or idx >= len(self.metadata):
                    continue
                results.append({"score": float(score), **self.metadata[idx]})
            return results

    def save(self, index_path: str | Path, metadata_path: str | Path, vectors_path: str | Path) -> None:
        if not self.ready:
            raise RuntimeError("Cannot save an empty vector store.")
        index_path, metadata_path, vectors_path = map(Path, (index_path, metadata_path, vectors_path))
        for path in (index_path, metadata_path, vectors_path):
            path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            payload = {
                "index_type": self.index_type,
                "dimension": self.dimension,
                "backend": self.backend,
                "metadata": self.metadata,
            }
            metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            if self.index is not None and faiss is not None:
                faiss.write_index(self.index, str(index_path))
                if vectors_path.exists():
                    vectors_path.unlink()
            else:
                np.save(vectors_path, self._numpy_vectors)

    @classmethod
    def load(
        cls,
        index_path: str | Path,
        metadata_path: str | Path,
        vectors_path: str | Path,
    ) -> FaissVectorStore:
        metadata_path = Path(metadata_path)
        if not metadata_path.exists():
            return cls()
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        store = cls(index_type=payload.get("index_type", "flat"))
        store.dimension = int(payload["dimension"])
        store.metadata = list(payload.get("metadata", []))
        index_path, vectors_path = Path(index_path), Path(vectors_path)
        if faiss is not None and index_path.exists():
            store.index = faiss.read_index(str(index_path))
        elif vectors_path.exists():
            store._numpy_vectors = np.load(vectors_path).astype("float32")
        else:
            # Metadata without vectors is not a usable index.
            store.dimension = None
            store.metadata = []
        return store

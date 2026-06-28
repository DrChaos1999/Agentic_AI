from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import HashingVectorizer

from app.retrieval.faiss_store import FaissVectorStore


class ManualFaissStore:
    """Local, deterministic text retrieval backed by FAISS and hashed TF features."""

    def __init__(self, n_features: int = 384) -> None:
        self.vectorizer = HashingVectorizer(
            n_features=n_features,
            alternate_sign=False,
            norm="l2",
            ngram_range=(1, 2),
            stop_words="english",
        )
        self.store = FaissVectorStore(index_type="flat")

    @staticmethod
    def _chunks(markdown: str) -> list[dict[str, str]]:
        chunks: list[dict[str, str]] = []
        heading = "General"
        buffer: list[str] = []
        for line in markdown.splitlines():
            if re.match(r"^#{1,3}\s+", line):
                if buffer:
                    text = "\n".join(buffer).strip()
                    if text:
                        chunks.append({"heading": heading, "text": text})
                heading = re.sub(r"^#{1,3}\s+", "", line).strip()
                buffer = []
            else:
                buffer.append(line)
        if buffer:
            text = "\n".join(buffer).strip()
            if text:
                chunks.append({"heading": heading, "text": text})
        return chunks

    def build_from_markdown(self, path: str | Path) -> None:
        path = Path(path)
        chunks = self._chunks(path.read_text(encoding="utf-8"))
        vectors = self.vectorizer.transform([f"{c['heading']} {c['text']}" for c in chunks]).toarray()
        self.store.build(vectors.astype("float32"), chunks)

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        if not self.store.ready or not query.strip():
            return []
        vector = self.vectorizer.transform([query]).toarray().astype("float32")
        return self.store.search(vector, top_k=top_k)

    def save(self, index_path: str | Path, metadata_path: str | Path) -> None:
        vectors_path = Path(metadata_path).with_suffix(".npy")
        self.store.save(index_path, metadata_path, vectors_path)

    @classmethod
    def load_or_build(
        cls,
        manual_path: str | Path,
        index_path: str | Path,
        metadata_path: str | Path,
    ) -> ManualFaissStore:
        instance = cls()
        vectors_path = Path(metadata_path).with_suffix(".npy")
        if Path(metadata_path).exists() and (Path(index_path).exists() or vectors_path.exists()):
            instance.store = FaissVectorStore.load(index_path, metadata_path, vectors_path)
            return instance
        instance.build_from_markdown(manual_path)
        instance.save(index_path, metadata_path)
        return instance

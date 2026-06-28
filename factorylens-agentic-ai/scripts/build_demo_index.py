from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np

from app.core.config import get_settings
from app.retrieval.faiss_store import FaissVectorStore
from app.vision.service import VisionService


def main() -> None:
    settings = get_settings()
    vision = VisionService(settings)
    vectors, metadata = [], []
    for path in sorted(Path("data/demo").rglob("*.png")):
        output = vision.predict_path(path)
        vectors.append(output.embedding)
        metadata.append(
            {
                "image_path": str(path),
                "label": path.parent.name,
                "incident_id": f"DEMO-{path.stem.upper()}",
                "machine_id": "DEMO-MACHINE",
                "resolution": "160x160",
                "source": "synthetic-smoke-test",
            }
        )
    if not vectors:
        raise SystemExit("Run python scripts/generate_demo_data.py first.")
    store = FaissVectorStore(settings.faiss_index_type)
    store.build(np.vstack(vectors), metadata)
    store.save(settings.faiss_index_path, settings.faiss_metadata_path, settings.faiss_vectors_path)
    print(f"Built demo index with {store.size} vectors using {store.backend}.")


if __name__ == "__main__":
    main()

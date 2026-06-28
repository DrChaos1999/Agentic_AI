from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from app.core.config import get_settings
from app.retrieval.faiss_store import FaissVectorStore
from app.vision.service import VisionService

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the image-embedding FAISS index.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed/train"))
    parser.add_argument("--index-type", choices=["flat", "hnsw", "ivf"], default="flat")
    parser.add_argument("--include-val", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    vision = VisionService(settings)
    roots = [args.data_dir]
    if args.include_val:
        roots.append(args.data_dir.parent / "val")
    vectors, metadata = [], []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            label = path.parent.name
            output = vision.predict_path(path)
            vectors.append(output.embedding)
            metadata.append(
                {
                    "image_path": str(path),
                    "label": label,
                    "source": root.name,
                    "resolution": f"{Image.open(path).width}x{Image.open(path).height}",
                    "model_version": output.model_version,
                }
            )
    if not vectors:
        raise SystemExit(f"No images found under {roots}.")
    store = FaissVectorStore(index_type=args.index_type)
    store.build(np.vstack(vectors).astype("float32"), metadata)
    store.save(settings.faiss_index_path, settings.faiss_metadata_path, settings.faiss_vectors_path)
    print(
        f"Built {store.backend} {store.index_type} index with {store.size} vectors "
        f"of dimension {store.dimension}."
    )


if __name__ == "__main__":
    main()

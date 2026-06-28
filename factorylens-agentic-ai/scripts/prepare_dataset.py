from __future__ import annotations

import argparse
import csv
import random
import shutil
from pathlib import Path

CLASS_MAP = {
    "MT_Blowhole": "blowhole",
    "MT_Break": "break",
    "MT_Crack": "crack",
    "MT_Fray": "fray",
    "MT_Free": "free",
    "MT_Uneven": "uneven",
}


def split_items(items: list[Path], seed: int, train_ratio: float, val_ratio: float):
    rng = random.Random(seed)
    items = list(items)
    rng.shuffle(items)
    train_end = int(len(items) * train_ratio)
    val_end = train_end + int(len(items) * val_ratio)
    return {"train": items[:train_end], "val": items[train_end:val_end], "test": items[val_end:]}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create stratified ImageFolder train/val/test splits.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/magnetic_tile"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.train_ratio + args.val_ratio >= 1:
        raise SystemExit("train_ratio + val_ratio must be less than 1.")
    if args.force and args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    for source_class, target_class in CLASS_MAP.items():
        images = sorted((args.raw_dir / source_class / "Imgs").glob("*.jpg"))
        if not images:
            raise SystemExit(f"No JPG images found for {source_class}. Download and validate first.")
        splits = split_items(images, args.seed, args.train_ratio, args.val_ratio)
        for split, paths in splits.items():
            destination = args.output_dir / split / target_class
            destination.mkdir(parents=True, exist_ok=True)
            for path in paths:
                target = destination / path.name
                shutil.copy2(path, target)
                manifest.append({"split": split, "class": target_class, "source": str(path), "path": str(target)})

    manifest_path = args.output_dir / "split_manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=["split", "class", "source", "path"])
        writer.writeheader()
        writer.writerows(manifest)
    print(f"Prepared {len(manifest)} images at {args.output_dir}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()

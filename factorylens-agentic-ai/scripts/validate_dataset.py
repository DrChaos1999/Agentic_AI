from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image, UnidentifiedImageError

EXPECTED_COUNTS = {
    "MT_Blowhole": 115,
    "MT_Break": 85,
    "MT_Crack": 57,
    "MT_Fray": 32,
    "MT_Free": 952,
    "MT_Uneven": 103,
}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(root: Path, strict_counts: bool = True) -> dict:
    rows = []
    class_counts: Counter[str] = Counter()
    corrupt = []
    hashes: dict[str, list[str]] = {}
    missing_masks = []

    for class_name in EXPECTED_COUNTS:
        image_dir = root / class_name / "Imgs"
        for path in sorted(image_dir.glob("*.jpg")):
            class_counts[class_name] += 1
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    width, height = image.size
                    mode = image.mode
            except (UnidentifiedImageError, OSError) as exc:
                corrupt.append({"path": str(path), "error": str(exc)})
                continue
            checksum = file_hash(path)
            hashes.setdefault(checksum, []).append(str(path))
            mask_path = path.with_suffix(".png")
            if class_name != "MT_Free" and not mask_path.exists():
                missing_masks.append(str(mask_path))
            rows.append(
                {
                    "path": str(path),
                    "class": class_name,
                    "width": width,
                    "height": height,
                    "mode": mode,
                    "sha256": checksum,
                    "mask_path": str(mask_path) if mask_path.exists() else "",
                }
            )

    duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]
    count_mismatches = {
        key: {"expected": expected, "actual": class_counts.get(key, 0)}
        for key, expected in EXPECTED_COUNTS.items()
        if class_counts.get(key, 0) != expected
    }
    result = {
        "valid": not corrupt and not missing_masks and (not strict_counts or not count_mismatches),
        "root": str(root),
        "expected_total": sum(EXPECTED_COUNTS.values()),
        "actual_total": sum(class_counts.values()),
        "class_counts": dict(class_counts),
        "count_mismatches": count_mismatches,
        "corrupt_images": corrupt,
        "missing_masks": missing_masks,
        "duplicate_groups": duplicate_groups,
        "records": rows,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate counts, readability, masks and duplicates.")
    parser.add_argument("--root", type=Path, default=Path("data/raw/magnetic_tile"))
    parser.add_argument("--report-dir", type=Path, default=Path("data/reports"))
    parser.add_argument("--non-strict-counts", action="store_true")
    args = parser.parse_args()
    result = validate(args.root, strict_counts=not args.non_strict_counts)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.report_dir / "dataset_validation.json"
    manifest_path = args.report_dir / "dataset_manifest.csv"
    serializable = {key: value for key, value in result.items() if key != "records"}
    report_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    with manifest_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=result["records"][0].keys() if result["records"] else ["path"])
        writer.writeheader()
        writer.writerows(result["records"])
    print(json.dumps(serializable, indent=2))
    if not result["valid"]:
        raise SystemExit("Dataset validation failed. Inspect data/reports/dataset_validation.json")
    print(f"Dataset validated. Reports: {report_path}, {manifest_path}")


if __name__ == "__main__":
    main()

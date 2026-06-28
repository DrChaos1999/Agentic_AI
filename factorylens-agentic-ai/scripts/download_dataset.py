from __future__ import annotations

import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path

import requests

SOURCE_URL = "https://github.com/abin24/Magnetic-tile-defect-datasets./archive/refs/heads/master.zip"
EXPECTED_ROOT = "Magnetic-tile-defect-datasets.-master"


def download(url: str, destination: Path) -> None:
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("wb") as output:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output.write(chunk)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the author-published Magnetic Tile dataset.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/magnetic_tile"))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.force:
        print(f"Dataset already exists at {args.output_dir}; use --force to replace it.")
        return
    if args.force and args.output_dir.exists():
        shutil.rmtree(args.output_dir)
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / "magnetic_tile.zip"
        print(f"Downloading from {SOURCE_URL}")
        download(SOURCE_URL, archive)
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(temp)
        extracted = Path(temp) / EXPECTED_ROOT
        if not extracted.exists():
            candidates = [p for p in Path(temp).iterdir() if p.is_dir()]
            if len(candidates) != 1:
                raise RuntimeError("Could not identify the extracted dataset root.")
            extracted = candidates[0]
        args.output_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(extracted, args.output_dir)
    print(f"Downloaded dataset to {args.output_dir}")
    print("Next: python scripts/validate_dataset.py && python scripts/prepare_dataset.py")


if __name__ == "__main__":
    main()

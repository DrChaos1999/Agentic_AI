from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

CLASSES = ["blowhole", "break", "crack", "fray", "free", "uneven"]


def create_pattern(label: str, index: int, size: int = 160) -> Image.Image:
    rng = np.random.default_rng(1000 + index + CLASSES.index(label) * 100)
    base = np.tile(np.linspace(70, 190, size, dtype=np.float32), (size, 1))
    base += rng.normal(0, 8, (size, size))
    image = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), mode="L")
    draw = ImageDraw.Draw(image)
    if label == "blowhole":
        for _ in range(5):
            x, y = rng.integers(20, size - 20, 2)
            r = int(rng.integers(5, 14))
            draw.ellipse((x-r, y-r, x+r, y+r), fill=int(rng.integers(20, 60)))
    elif label == "break":
        draw.rectangle((size // 2 - 8, 0, size // 2 + 10, size), fill=25)
    elif label == "crack":
        points = [(10, size // 2)]
        for x in range(20, size, 18):
            points.append((x, size // 2 + int(25 * math.sin(x / 15)) + int(rng.integers(-8, 9))))
        draw.line(points, fill=15, width=3)
    elif label == "fray":
        for y in range(10, size, 12):
            draw.line((0, y, int(rng.integers(25, 60)), y + int(rng.integers(-8, 9))), fill=20, width=2)
    elif label == "uneven":
        for y in range(0, size, 16):
            draw.rectangle((0, y, size, y + 7), fill=int(80 + (y % 40) * 2))
    return image.filter(ImageFilter.GaussianBlur(0.4)).convert("RGB")


def main() -> None:
    root = Path("data/demo")
    for label in CLASSES:
        directory = root / label
        directory.mkdir(parents=True, exist_ok=True)
        for index in range(6):
            create_pattern(label, index).save(directory / f"{label}_{index:02d}.png")
    print(f"Generated {len(CLASSES) * 6} synthetic smoke-test images in {root}")


if __name__ == "__main__":
    main()

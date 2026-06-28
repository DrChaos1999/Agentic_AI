from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

from app.vision.model import load_checkpoint
from app.vision.transforms import inference_transform


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=Path("models/factorylens_resnet18.pt"))
    parser.add_argument("--test-dir", type=Path, default=Path("data/processed/test"))
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output", type=Path, default=Path("artifacts/evaluation/metrics.json"))
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    loaded = load_checkpoint(args.checkpoint, device)
    dataset = ImageFolder(args.test_dir, transform=inference_transform(loaded.image_size))
    if dataset.classes != loaded.class_names:
        raise ValueError("Checkpoint class order does not match test data folders.")
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False)
    true, predicted = [], []
    with torch.inference_mode():
        for images, labels in loader:
            logits = loaded.model(images.to(device))
            true.extend(labels.tolist())
            predicted.extend(logits.argmax(dim=1).cpu().tolist())
    report = classification_report(true, predicted, target_names=dataset.classes, output_dict=True, zero_division=0)
    payload = {
        "classification_report": report,
        "confusion_matrix": confusion_matrix(true, predicted).tolist(),
        "accuracy": float(np.mean(np.array(true) == np.array(predicted))),
        "samples": len(dataset),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

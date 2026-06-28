from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import matplotlib.pyplot as plt
import mlflow
import mlflow.pytorch
import numpy as np
import torch
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
from torchvision.datasets import ImageFolder

from app.vision.model import TransferLearningClassifier, save_checkpoint
from app.vision.transforms import inference_transform, training_transform
from training.common import save_json, seed_everything


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fine-tune ResNet-18 on the prepared defect dataset.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    parser.add_argument("--output", type=Path, default=Path("models/factorylens_resnet18.pt"))
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--freeze-backbone", action="store_true")
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--tracking-uri", default="sqlite:///./mlflow.db")
    parser.add_argument("--experiment", default="factorylens-defect-classification")
    parser.add_argument("--register-model", action="store_true")
    parser.add_argument("--registered-model-name", default="FactoryLensDefectClassifier")
    return parser.parse_args()


def run_epoch(model, loader, criterion, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    labels_all, predictions_all = [], []
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)
        logits = model(images)
        loss = criterion(logits, labels)
        if training:
            loss.backward()
            optimizer.step()
        total_loss += loss.item() * images.size(0)
        labels_all.extend(labels.cpu().tolist())
        predictions_all.extend(logits.argmax(dim=1).cpu().tolist())
    return {
        "loss": total_loss / len(loader.dataset),
        "accuracy": float(np.mean(np.array(labels_all) == np.array(predictions_all))),
        "macro_f1": float(f1_score(labels_all, predictions_all, average="macro", zero_division=0)),
        "labels": labels_all,
        "predictions": predictions_all,
    }


def main() -> None:
    args = parse_args()
    seed_everything(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train_dataset = ImageFolder(args.data_dir / "train", transform=training_transform(args.image_size))
    val_dataset = ImageFolder(args.data_dir / "val", transform=inference_transform(args.image_size))
    if train_dataset.classes != val_dataset.classes:
        raise ValueError("Train and validation class folders do not match.")

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        pin_memory=torch.cuda.is_available(),
    )

    model = TransferLearningClassifier(
        num_classes=len(train_dataset.classes), pretrained=not args.no_pretrained
    ).to(device)
    if args.freeze_backbone:
        for parameter in model.backbone.parameters():
            parameter.requires_grad = False

    counts = np.bincount(train_dataset.targets, minlength=len(train_dataset.classes))
    weights = counts.sum() / np.maximum(counts, 1)
    weights = weights / weights.mean()
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
    optimizer = AdamW(
        [parameter for parameter in model.parameters() if parameter.requires_grad],
        lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment)
    best_f1 = -1.0
    history = []
    start = time.perf_counter()

    with mlflow.start_run() as run:
        mlflow.log_params(
            {
                "backbone": "resnet18",
                "epochs": args.epochs,
                "batch_size": args.batch_size,
                "learning_rate": args.learning_rate,
                "weight_decay": args.weight_decay,
                "image_size": args.image_size,
                "freeze_backbone": args.freeze_backbone,
                "pretrained": not args.no_pretrained,
                "seed": args.seed,
                "classes": json.dumps(train_dataset.classes),
                "train_images": len(train_dataset),
                "val_images": len(val_dataset),
                "device": str(device),
            }
        )
        for epoch in range(1, args.epochs + 1):
            train_metrics = run_epoch(model, train_loader, criterion, device, optimizer)
            val_metrics = run_epoch(model, val_loader, criterion, device)
            history.append({"epoch": epoch, "train": train_metrics, "val": val_metrics})
            for prefix, metrics in (("train", train_metrics), ("val", val_metrics)):
                for key in ("loss", "accuracy", "macro_f1"):
                    mlflow.log_metric(f"{prefix}_{key}", metrics[key], step=epoch)
            if val_metrics["macro_f1"] > best_f1:
                best_f1 = val_metrics["macro_f1"]
                save_checkpoint(
                    args.output,
                    model,
                    train_dataset.classes,
                    args.image_size,
                    model_version=run.info.run_id,
                    extra={"best_val_macro_f1": best_f1},
                )
            print(
                f"Epoch {epoch:02d}: train_loss={train_metrics['loss']:.4f} "
                f"val_loss={val_metrics['loss']:.4f} val_f1={val_metrics['macro_f1']:.4f}"
            )

        loaded = torch.load(args.output, map_location=device, weights_only=False)
        model.load_state_dict(loaded["state_dict"])
        final = run_epoch(model, val_loader, criterion, device)
        report = classification_report(
            final["labels"], final["predictions"], target_names=train_dataset.classes, output_dict=True, zero_division=0
        )
        matrix = confusion_matrix(final["labels"], final["predictions"])
        artifacts = Path("artifacts/training")
        artifacts.mkdir(parents=True, exist_ok=True)
        report_path = artifacts / "classification_report.json"
        save_json(report_path, report)
        fig, ax = plt.subplots(figsize=(8, 6))
        image = ax.imshow(matrix)
        ax.figure.colorbar(image, ax=ax)
        ax.set_xticks(range(len(train_dataset.classes)), train_dataset.classes, rotation=45, ha="right")
        ax.set_yticks(range(len(train_dataset.classes)), train_dataset.classes)
        ax.set_xlabel("Predicted")
        ax.set_ylabel("True")
        fig.tight_layout()
        confusion_path = artifacts / "confusion_matrix.png"
        fig.savefig(confusion_path, dpi=160)
        plt.close(fig)

        mlflow.log_artifact(str(report_path))
        mlflow.log_artifact(str(confusion_path))
        mlflow.log_artifact(str(args.output), artifact_path="checkpoints")
        mlflow.log_metric("best_val_macro_f1", best_f1)
        mlflow.log_metric("training_seconds", time.perf_counter() - start)
        # This custom module exposes both logits and embeddings. MLflow's PT2
        # exporter currently applies dynamic-batch assumptions that can fail
        # for some torchvision backbones, so the project uses pickle explicitly.
        # Only load model artifacts that you created or trust.
        model_to_log = model.to("cpu").eval()
        model_info = mlflow.pytorch.log_model(
            model_to_log,
            name="model",
            registered_model_name=args.registered_model_name if args.register_model else None,
            serialization_format="pickle",
            pip_requirements=[
                "torch>=2.5,<3",
                "torchvision>=0.20,<1",
                "numpy>=1.26,<3",
            ],
        )
        print(f"Best checkpoint: {args.output}")
        print(f"MLflow run: {run.info.run_id}")
        print(f"Logged model: {model_info.model_uri}")


if __name__ == "__main__":
    main()

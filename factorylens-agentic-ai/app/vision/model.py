from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch import nn
from torchvision.models import ResNet18_Weights, resnet18

DEFAULT_CLASSES = ["blowhole", "break", "crack", "fray", "free", "uneven"]


class TransferLearningClassifier(nn.Module):
    """ResNet-18 transfer-learning model with an exposed embedding layer."""

    def __init__(self, num_classes: int, pretrained: bool = True) -> None:
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        backbone = resnet18(weights=weights)
        embedding_dim = backbone.fc.in_features
        backbone.fc = nn.Identity()
        self.backbone = backbone
        self.classifier = nn.Linear(embedding_dim, num_classes)
        self.embedding_dim = embedding_dim

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.forward_features(x))


@dataclass(slots=True)
class LoadedModel:
    model: TransferLearningClassifier
    class_names: list[str]
    image_size: int
    model_version: str


def save_checkpoint(
    path: str | Path,
    model: TransferLearningClassifier,
    class_names: list[str],
    image_size: int,
    model_version: str,
    extra: dict | None = None,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "state_dict": model.state_dict(),
            "class_names": class_names,
            "image_size": image_size,
            "model_version": model_version,
            "extra": extra or {},
        },
        path,
    )


def load_checkpoint(path: str | Path, device: torch.device) -> LoadedModel:
    payload = torch.load(Path(path), map_location=device, weights_only=False)
    class_names = list(payload.get("class_names", DEFAULT_CLASSES))
    model = TransferLearningClassifier(num_classes=len(class_names), pretrained=False)
    model.load_state_dict(payload["state_dict"])
    model.to(device).eval()
    return LoadedModel(
        model=model,
        class_names=class_names,
        image_size=int(payload.get("image_size", 224)),
        model_version=str(payload.get("model_version", "local-checkpoint")),
    )

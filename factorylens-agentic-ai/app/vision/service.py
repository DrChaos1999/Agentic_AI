from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageFilter

from app.core.config import Settings
from app.vision.model import DEFAULT_CLASSES, LoadedModel, load_checkpoint
from app.vision.transforms import inference_transform


@dataclass(slots=True)
class VisionOutput:
    predicted_class: str
    confidence: float
    probabilities: dict[str, float]
    embedding: np.ndarray
    model_version: str
    model_status: str


class VisionService:
    """Loads a trained checkpoint or uses a transparent deterministic demo mode."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.device = self._resolve_device(settings.device)
        self.loaded: LoadedModel | None = None
        if settings.model_path.exists():
            self.loaded = load_checkpoint(settings.model_path, self.device)
        elif not settings.demo_mode:
            raise FileNotFoundError(
                f"No checkpoint found at {settings.model_path}. Train the model or set DEMO_MODE=true."
            )

    @staticmethod
    def _resolve_device(value: str) -> torch.device:
        if value != "auto":
            return torch.device(value)
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    @property
    def ready(self) -> bool:
        return self.loaded is not None or self.settings.demo_mode

    @property
    def class_names(self) -> list[str]:
        return self.loaded.class_names if self.loaded else DEFAULT_CLASSES

    @property
    def embedding_dimension(self) -> int:
        return self.loaded.model.embedding_dim if self.loaded else 256

    def predict_path(self, image_path: str | Path) -> VisionOutput:
        with Image.open(image_path) as image:
            return self.predict(image.convert("RGB"))

    def predict(self, image: Image.Image) -> VisionOutput:
        if self.loaded:
            return self._predict_model(image)
        return self._predict_demo(image)

    def _predict_model(self, image: Image.Image) -> VisionOutput:
        assert self.loaded is not None
        transform = inference_transform(self.loaded.image_size)
        batch = transform(image.convert("RGB")).unsqueeze(0).to(self.device)
        with torch.inference_mode():
            embedding_tensor = self.loaded.model.forward_features(batch)
            logits = self.loaded.model.classifier(embedding_tensor)
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()
            embedding = embedding_tensor[0].cpu().numpy().astype("float32")
        index = int(np.argmax(probabilities))
        return VisionOutput(
            predicted_class=self.loaded.class_names[index],
            confidence=float(probabilities[index]),
            probabilities={
                label: float(probabilities[i]) for i, label in enumerate(self.loaded.class_names)
            },
            embedding=embedding,
            model_version=self.loaded.model_version,
            model_status="trained-checkpoint",
        )

    def _predict_demo(self, image: Image.Image) -> VisionOutput:
        """Deterministic smoke-test mode; predictions are explicitly marked untrained."""
        gray = image.convert("L").resize((16, 16))
        array = np.asarray(gray, dtype=np.float32) / 255.0
        embedding = array.reshape(-1).astype("float32")
        norm = np.linalg.norm(embedding)
        if norm:
            embedding /= norm

        blurred = gray.filter(ImageFilter.GaussianBlur(radius=1.2))
        edges = np.asarray(gray, dtype=np.float32) - np.asarray(blurred, dtype=np.float32)
        features = np.array(
            [array.mean(), array.std(), np.abs(edges).mean() / 255.0, np.percentile(array, 90)],
            dtype=np.float32,
        )
        digest = hashlib.sha256(features.tobytes()).digest()
        chosen = digest[0] % len(DEFAULT_CLASSES)
        raw = np.array([1.0 + digest[i + 1] / 255.0 for i in range(len(DEFAULT_CLASSES))])
        raw[chosen] += 1.8
        probs = np.exp(raw - raw.max())
        probs /= probs.sum()
        return VisionOutput(
            predicted_class=DEFAULT_CLASSES[chosen],
            confidence=float(probs[chosen]),
            probabilities={label: float(probs[i]) for i, label in enumerate(DEFAULT_CLASSES)},
            embedding=embedding,
            model_version="demo-feature-extractor-v1",
            model_status="demo-untrained-do-not-use-for-production",
        )

    def info(self) -> dict[str, object]:
        return {
            "ready": self.ready,
            "device": str(self.device),
            "class_names": self.class_names,
            "embedding_dimension": self.embedding_dimension,
            "model_path": str(self.settings.model_path),
            "status": "trained-checkpoint" if self.loaded else "demo-untrained",
            "model_version": self.loaded.model_version if self.loaded else "demo-feature-extractor-v1",
        }

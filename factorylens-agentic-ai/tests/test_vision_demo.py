
from PIL import Image

from app.core.config import Settings
from app.vision.service import VisionService


def test_demo_vision_is_deterministic(tmp_path):
    path = tmp_path / "image.png"
    Image.new("RGB", (64, 64), color=(100, 100, 100)).save(path)
    settings = Settings(demo_mode=True, model_path=tmp_path / "missing.pt")
    service = VisionService(settings)
    first = service.predict_path(path)
    second = service.predict_path(path)
    assert first.predicted_class == second.predicted_class
    assert first.embedding.shape == (256,)
    assert "demo-untrained" in first.model_status

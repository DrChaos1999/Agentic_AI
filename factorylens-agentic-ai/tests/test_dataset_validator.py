from pathlib import Path

from PIL import Image

from scripts.validate_dataset import validate


def test_validator_detects_readable_non_strict_dataset(tmp_path: Path):
    root = tmp_path / "dataset"
    for class_name in ["MT_Blowhole", "MT_Break", "MT_Crack", "MT_Fray", "MT_Free", "MT_Uneven"]:
        directory = root / class_name / "Imgs"
        directory.mkdir(parents=True)
        image_path = directory / "sample.jpg"
        Image.new("L", (20, 20), color=120).save(image_path)
        if class_name != "MT_Free":
            Image.new("L", (20, 20), color=255).save(image_path.with_suffix(".png"))
    result = validate(root, strict_counts=False)
    assert result["valid"]
    assert result["actual_total"] == 6

from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/bmp", "image/tiff"}


def save_validated_upload(upload: UploadFile, directory: Path, max_upload_mb: int) -> Path:
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, BMP, or TIFF image.")
    suffix = Path(upload.filename or "image.jpg").suffix.lower() or ".jpg"
    destination = directory / f"{uuid4()}{suffix}"
    directory.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as output:
        shutil.copyfileobj(upload.file, output)
    if destination.stat().st_size > max_upload_mb * 1024 * 1024:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=413, detail=f"Maximum upload size is {max_upload_mb} MB.")
    try:
        with Image.open(destination) as image:
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        destination.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="The uploaded file is not a readable image.") from exc
    return destination

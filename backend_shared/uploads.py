from __future__ import annotations

import shutil
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from botocore.exceptions import BotoCoreError, ClientError
import boto3

from backend_shared.config import get_settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def get_upload_directory() -> Path:
    settings = get_settings()
    upload_dir = Path(settings.uploads_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def s3_uploads_enabled() -> bool:
    return bool(get_settings().s3_bucket_name)


def _s3_key(filename: str) -> str:
    settings = get_settings()
    prefix = settings.s3_prefix.strip("/")
    return f"{prefix}/{filename}" if prefix else filename


def _s3_client():
    settings = get_settings()
    return boto3.client("s3", region_name=settings.s3_region)


def _safe_filename(filename: str) -> str:
    if not filename or Path(filename).name != filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid image filename")
    return filename


def save_upload(file: UploadFile):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    extension = Path(file.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    content_type = file.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    filename = f"{uuid4().hex}{extension}"
    settings = get_settings()

    if settings.s3_bucket_name:
        try:
            _s3_client().upload_fileobj(
                file.file,
                settings.s3_bucket_name,
                _s3_key(filename),
                ExtraArgs={"ContentType": content_type},
            )
        except (BotoCoreError, ClientError) as exc:
            raise HTTPException(status_code=502, detail="Could not upload image to S3") from exc
    else:
        destination = get_upload_directory() / filename

        with destination.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)


    return {
        "url": f"/api/user/uploads/{filename}",
        "filename": filename,
    }


def load_upload(filename: str):
    filename = _safe_filename(filename)
    settings = get_settings()

    if settings.s3_bucket_name:
        try:
            response = _s3_client().get_object(Bucket=settings.s3_bucket_name, Key=_s3_key(filename))
            return {
                "body": response["Body"].read(),
                "content_type": response.get("ContentType") or "application/octet-stream",
            }
        except ClientError as exc:
            status_code = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status_code == 404:
                raise HTTPException(status_code=404, detail="Image not found") from exc
            raise HTTPException(status_code=502, detail="Could not read image from S3") from exc
        except BotoCoreError as exc:
            raise HTTPException(status_code=502, detail="Could not read image from S3") from exc

    path = get_upload_directory() / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    return {
        "body": path.read_bytes(),
        "content_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
    }

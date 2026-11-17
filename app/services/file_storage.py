from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/zip",
}

CHUNK_SIZE = 1024 * 1024


class FileTooLargeError(Exception):
    pass


class UnsupportedFileTypeError(Exception):
    pass


def _upload_dir() -> Path:
    path = Path(settings.upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(file: UploadFile) -> tuple[str, int]:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedFileTypeError(file.content_type)

    extension = Path(file.filename or "").suffix.lower()[:10]
    stored_name = f"{uuid4().hex}{extension}"
    destination = _upload_dir() / stored_name
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    size = 0
    too_large = False
    with destination.open("wb") as output:
        while chunk := file.file.read(CHUNK_SIZE):
            size += len(chunk)
            if size > max_bytes:
                too_large = True
                break
            output.write(chunk)

    if too_large:
        destination.unlink(missing_ok=True)
        raise FileTooLargeError(settings.max_upload_size_mb)

    return stored_name, size


def get_file_path(stored_name: str) -> Path:
    return _upload_dir() / stored_name


def delete_file(stored_name: str) -> None:
    get_file_path(stored_name).unlink(missing_ok=True)


def delete_files(stored_names: list[str]) -> None:
    for stored_name in stored_names:
        delete_file(stored_name)

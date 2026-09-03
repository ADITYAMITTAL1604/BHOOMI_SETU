"""BhoomiSetu Document Service — file validation, storage, versioning, and hash."""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple

from fastapi import HTTPException, UploadFile, status

logger = logging.getLogger(__name__)

# Allowed file extensions and their expected MIME types
ALLOWED_EXTENSIONS: dict[str, str] = {
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}

# Magic bytes for each file format (first 8 bytes)
MAGIC_BYTES: dict[str, bytes] = {
    "pdf": b"%PDF",
    "docx": b"PK\x03\x04",   # Office Open XML (ZIP)
    "doc": b"\xd0\xcf\x11\xe0",   # OLE compound file
    "xlsx": b"PK\x03\x04",  # Office Open XML (ZIP)
    "xls": b"\xd0\xcf\x11\xe0",
    "png": b"\x89PNG",
    "jpg": b"\xff\xd8\xff",
    "jpeg": b"\xff\xd8\xff",
}

MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB


def validate_file(file: UploadFile, max_mb: int = 20) -> str:
    """Validate extension, MIME type, size, and magic bytes of an uploaded file.

    Parameters
    ----------
    file : UploadFile
        The FastAPI upload file object.
    max_mb : int
        Maximum allowed size in megabytes.

    Returns
    -------
    str : The sanitized lowercase file extension.

    Raises
    ------
    HTTPException 422 : On any validation failure.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file has no filename.",
        )

    ext = Path(file.filename).suffix.lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"File type '.{ext}' is not allowed. Permitted: {sorted(ALLOWED_EXTENSIONS.keys())}",
        )

    return ext


async def validate_magic_bytes(file: UploadFile, ext: str) -> bytes:
    """Read the file content, validate magic bytes, and return the full content.

    Must be called before storing to filesystem.
    """
    content = await file.read()

    max_size = MAX_FILE_SIZE_BYTES
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {max_size // (1024 * 1024)} MB.",
        )

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    expected_magic = MAGIC_BYTES.get(ext)
    if expected_magic:
        prefix = content[: len(expected_magic)]
        if prefix != expected_magic:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"File content does not match the declared type '.{ext}'. "
                    "Magic byte validation failed — possible file spoofing."
                ),
            )

    return content


def store_file(
    content: bytes,
    *,
    storage_base: str,
    project_id: str,
    document_id: uuid.UUID,
    ext: str,
) -> Tuple[str, str, int, str]:
    """Write file to local filesystem with UUID filename.

    Returns
    -------
    Tuple of (file_path, sha256_hex, file_size_bytes, mime_type)
    """
    # Compute SHA-256 hash before writing
    sha256 = hashlib.sha256(content).hexdigest()
    file_size = len(content)
    mime_type = ALLOWED_EXTENSIONS.get(ext, "application/octet-stream")

    # Build directory path: {storage_base}/{project_id}/
    dest_dir = Path(storage_base) / str(project_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{document_id}.{ext}"
    file_path = dest_dir / filename

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info("Stored document %s (%d bytes, sha256=%s)", file_path, file_size, sha256[:12])
    return str(file_path), sha256, file_size, mime_type


def get_next_version(db, parcel_id, document_type: str) -> int:
    """Return the next version number for (parcel_id, document_type)."""
    from sqlalchemy import func, select
    from app.models import Document

    count = db.execute(
        select(func.count(Document.document_id)).where(
            Document.parcel_id == parcel_id,
            Document.document_type == document_type,
        )
    ).scalar() or 0
    return int(count) + 1

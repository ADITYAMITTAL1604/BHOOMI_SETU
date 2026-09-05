"""FastAPI router for /documents — upload, download, list, and delete endpoints."""

from __future__ import annotations

import os
import uuid as _uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select, and_, or_
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.deps import get_current_user, require_state_or_above, get_user_geographic_scope
from app.database import get_db
from app.models import Document, Parcel, Project
from app.models.enums import DocumentType

router = APIRouter()


# ── Scope helper ──────────────────────────────────────────────────────────────

def _document_in_scope(db: Session, doc: Document, current_user) -> bool:
    """Return True if the document's linked parcel/project is within the
    current user's geographic scope. Documents with no location (project_id
    and parcel_id both null) are treated as system-wide and always visible.
    """
    scope = get_user_geographic_scope(current_user)
    if not scope:
        return True  # Unscoped (national) role — sees everything.

    state = None
    district = None

    if doc.parcel_id:
        parcel = db.execute(
            select(Parcel).where(Parcel.parcel_id == doc.parcel_id)
        ).scalar_one_or_none()
        if parcel:
            state = parcel.state or None
            district = parcel.district or None
    elif doc.project_id:
        project = db.execute(
            select(Project).where(Project.project_id == doc.project_id)
        ).scalar_one_or_none()
        if project:
            if project.states:
                state = project.states[0]
            if project.districts:
                district = project.districts[0]

    if state is None and district is None:
        return True  # No location on the document — treat as system-wide.

    if scope.get("district"):
        return district == scope["district"]
    if scope.get("state"):
        return state == scope["state"]
    return True


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    summary="Upload a document with magic-byte validation and SHA-256 hash",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    project_id: Optional[UUID] = Form(None),
    parcel_id: Optional[UUID] = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Upload a document file with:
    - Extension and MIME type validation
    - Magic byte (file signature) verification
    - 20 MB size limit
    - SHA-256 integrity hash
    - UUID-renamed storage
    - Version tracking per (parcel_id, document_type)
    """
    from app.services.document_service import (
        validate_file,
        validate_magic_bytes,
        store_file,
        get_next_version,
    )

    settings = get_settings()

    # 1. Validate extension
    ext = validate_file(file)

    # 2. Read content and validate magic bytes + size
    content = await validate_magic_bytes(file, ext)

    # 3. Determine version
    version = 1
    if parcel_id:
        version = get_next_version(db, parcel_id, document_type)

    # 4. Store on filesystem
    doc_id = _uuid.uuid4()
    effective_project_id = project_id or (
        db.execute(select(Parcel.project_id).where(Parcel.parcel_id == parcel_id)).scalar()
        if parcel_id else None
    )

    file_path, sha256, file_size, mime_type = store_file(
        content,
        storage_base=settings.document_storage_path,
        project_id=str(effective_project_id or "unknown"),
        document_id=doc_id,
        ext=ext,
    )

    # 5. Persist Document record
    doc = Document(
        document_id=doc_id,
        project_id=effective_project_id,
        parcel_id=parcel_id,
        uploaded_by=current_user.id,
        document_type=document_type,
        title=title,
        description=description,
        file_path=file_path,
        file_size_bytes=file_size,
        mime_type=mime_type,
        metadata_json={
            "sha256": sha256,
            "version": version,
            "original_filename": file.filename,
        },
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "document_id": str(doc.document_id),
        "title": doc.title,
        "document_type": doc.document_type,
        "mime_type": doc.mime_type,
        "file_size_bytes": doc.file_size_bytes,
        "sha256": sha256,
        "version": version,
        "project_id": str(doc.project_id) if doc.project_id else None,
        "parcel_id": str(doc.parcel_id) if doc.parcel_id else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else datetime.now(timezone.utc).isoformat(),
    }


# ── Download ──────────────────────────────────────────────────────────────────

@router.get(
    "/{document_id}/download",
    summary="Download a document (authenticated, role-checked)",
)
def download_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Stream document file with correct Content-Type and Content-Disposition headers."""
    doc = db.execute(
        select(Document).where(Document.document_id == document_id)
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not _document_in_scope(db, doc, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: this document belongs to a project/parcel outside your assigned scope.",
        )

    if not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=404,
            detail="Document file is no longer available on storage.",
        )

    filename = f"{doc.title.replace(' ', '_')}.{Path(doc.file_path).suffix.lstrip('.')}"
    return FileResponse(
        path=doc.file_path,
        media_type=doc.mime_type,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get(
    "",
    summary="List documents with filters",
    response_model=dict,
)
def list_documents(
    project_id: Optional[UUID] = Query(None),
    parcel_id: Optional[UUID] = Query(None),
    document_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return paginated document list filtered by project, parcel, type, and
    the current user's geographic scope."""
    stmt = select(Document)
    if project_id:
        stmt = stmt.where(Document.project_id == project_id)
    if parcel_id:
        stmt = stmt.where(Document.parcel_id == parcel_id)
    if document_type:
        stmt = stmt.where(Document.document_type == document_type)

    scope = get_user_geographic_scope(current_user)
    if scope:
        from app.core.deps import filter_by_geographic_scope

        no_location = Document.project_id.is_(None) & Document.parcel_id.is_(None)
        project_conditions = filter_by_geographic_scope(current_user, Project)
        parcel_conditions = filter_by_geographic_scope(current_user, Parcel)

        in_scope_clauses = [no_location]
        if project_conditions:
            stmt = stmt.outerjoin(Project, Document.project_id == Project.project_id)
            in_scope_clauses.append(and_(Document.project_id.isnot(None), *project_conditions))
        if parcel_conditions:
            stmt = stmt.outerjoin(Parcel, Document.parcel_id == Parcel.parcel_id)
            in_scope_clauses.append(and_(Document.parcel_id.isnot(None), *parcel_conditions))

        stmt = stmt.where(or_(*in_scope_clauses))

    stmt = stmt.order_by(Document.created_at.desc())
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    offset = (page - 1) * page_size
    docs = db.execute(stmt.offset(offset).limit(page_size)).scalars().all()

    return {
        "items": [
            {
                "document_id": str(d.document_id),
                "title": d.title,
                "document_type": d.document_type,
                "mime_type": d.mime_type,
                "file_size_bytes": d.file_size_bytes,
                "version": (d.metadata_json or {}).get("version", 1),
                "is_verified": d.is_verified,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "project_id": str(d.project_id) if d.project_id else None,
                "parcel_id": str(d.parcel_id) if d.parcel_id else None,
            }
            for d in docs
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": max(1, -(-total // page_size)),
        },
    }


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete(
    "/{document_id}",
    summary="Delete a document (admin/state-or-above)",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_state_or_above),
):
    """Remove document record and unlink from filesystem."""
    doc = db.execute(
        select(Document).where(Document.document_id == document_id)
    ).scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove from filesystem (best-effort)
    try:
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
    except OSError as e:
        import logging
        logging.getLogger(__name__).warning("Could not delete file %s: %s", doc.file_path, e)

    db.delete(doc)
    db.commit()

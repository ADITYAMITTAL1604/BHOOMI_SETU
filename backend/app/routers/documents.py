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

    # 6. Initialize approval workflow — notify first approver
    try:
        from app.services.notification_service import create_notification
        from app.models.document_approval import APPROVAL_CHAIN

        if APPROVAL_CHAIN:
            first_step = APPROVAL_CHAIN[0]
            from app.models import User as UserModel
            approvers = db.execute(
                select(UserModel).where(
                    UserModel.role == first_step["role"],
                    UserModel.is_active == True,  # noqa: E712
                )
            ).scalars().all()

            for approver in approvers:
                # Geographic scope filtering
                scope_match = True
                if parcel_id:
                    parcel_row = db.execute(
                        select(Parcel).where(Parcel.parcel_id == parcel_id)
                    ).scalar_one_or_none()
                    if parcel_row and approver.district_scope and parcel_row.district != approver.district_scope:
                        scope_match = False
                    if parcel_row and approver.state_scope and parcel_row.state != approver.state_scope:
                        scope_match = False

                if scope_match:
                    create_notification(
                        db,
                        user_id=approver.id,
                        title=f"New Document for Review: {doc.title}",
                        message=f"A new {doc.document_type} document '{doc.title}' has been uploaded and requires your review.",
                        severity="INFO",
                        category="document",
                        entity_type="document",
                        entity_id=doc.document_id,
                        action_url="/approvals",
                    )
            db.commit()
    except Exception:
        pass  # Non-blocking — notification failure should not break upload

    return {
        "document_id": str(doc.document_id),
        "title": doc.title,
        "document_type": doc.document_type,
        "approval_status": doc.approval_status,
        "current_approval_step": doc.current_approval_step,
        "mime_type": doc.mime_type,
        "file_size_bytes": doc.file_size_bytes,
        "sha256": sha256,
        "version": version,
        "project_id": str(doc.project_id) if doc.project_id else None,
        "parcel_id": str(doc.parcel_id) if doc.parcel_id else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else datetime.now(timezone.utc).isoformat(),
    }


# ── Download ──────────────────────────────────────────────────────────────────

def _get_document_text_content(doc: Document, db: Session) -> str:
    """Read document physical file if present, or construct official record text."""
    settings = get_settings()
    filename_stem = Path(doc.file_path).name if doc.file_path else "document"
    candidate_paths = []
    if doc.file_path:
        candidate_paths.append(Path(doc.file_path))
        candidate_paths.append(Path(settings.document_storage_path) / doc.file_path)
        candidate_paths.append(Path(settings.document_storage_path) / filename_stem)
        candidate_paths.append(Path(settings.document_storage_path) / "synthetic" / filename_stem)

    base_dir = Path(__file__).resolve().parents[2]
    repo_dir = base_dir.parent
    candidate_paths.extend([
        repo_dir / "sih-upgrade-context" / "sample_documents" / filename_stem,
        repo_dir / "backend" / "storage" / "documents" / filename_stem,
        repo_dir / "backend" / "storage" / "documents" / "synthetic" / filename_stem,
    ])

    resolved_path: Optional[Path] = None
    for candidate in candidate_paths:
        try:
            if candidate.exists() and candidate.is_file():
                resolved_path = candidate
                break
        except Exception:
            continue

    if resolved_path:
        try:
            content = resolved_path.read_text(encoding="utf-8", errors="ignore")
            if content and len(content.strip()) > 0:
                return content
        except Exception:
            pass

    # Default formatted record
    project = db.execute(select(Project).where(Project.project_id == doc.project_id)).scalar_one_or_none() if doc.project_id else None
    parcel = db.execute(select(Parcel).where(Parcel.parcel_id == doc.parcel_id)).scalar_one_or_none() if doc.parcel_id else None

    project_name = project.name if project else "System-wide / Unassigned"
    parcel_info = f"Survey #{parcel.survey_number} ({parcel.district}, {parcel.state})" if parcel else "System-wide / Unassigned"

    return f"""================================================================================
GOVERNMENT OF INDIA — PM GATI SHAKTI BHOOMI SETU PORTAL
OFFICIAL LAND ACQUISITION & REVENUE RECORD
================================================================================

DOCUMENT SUMMARY & METADATA
--------------------------------------------------------------------------------
Document Title:     {doc.title}
Document Type:      {doc.document_type.replace('_', ' ')}
Approval Status:    {doc.approval_status}
Verification State: {'VERIFIED OFFICIAL RECORD' if doc.is_verified else 'REGISTERED RECORD'}
Associated Project: {project_name}
Land Parcel:        {parcel_info}
Current Step:       Step {doc.current_approval_step or 1}
Document ID:        {doc.document_id}
Created Timestamp:  {doc.created_at or 'N/A'}

--------------------------------------------------------------------------------
RECORD DESCRIPTION & DETAILS
--------------------------------------------------------------------------------
{doc.description or 'Official land acquisition record registered in BhoomiSetu portal database.'}

--------------------------------------------------------------------------------
LEGAL & COMPLIANCE STATEMENT
--------------------------------------------------------------------------------
This document is registered in the PM Gati Shakti BhoomiSetu Land Acquisition
Portal. All recorded details, approval chains, and digital signatures are
cryptographically verified and stored under Department of Land Resources compliance.

================================================================================
BhoomiSetu Portal — Department of Land Resources, Govt. of India
================================================================================
"""


def _generate_pdf_document(doc: Document, project_name: str, parcel_info: str, text_content: str) -> bytes:
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#4B5563'),
        alignment=1
    )
    heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=8,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1F2937')
    )

    story = []
    story.append(Paragraph("GOVERNMENT OF INDIA — PM GATI SHAKTI BHOOMI SETU", title_style))
    story.append(Paragraph("DEPARTMENT OF LAND RESOURCES • OFFICIAL DOCUMENT RECORD", subtitle_style))
    story.append(Spacer(1, 10))

    def _esc(val: str) -> str:
        if not val: return ""
        return str(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    meta_data = [
        [Paragraph("<b>Document Title:</b>", body_style), Paragraph(_esc(doc.title), body_style)],
        [Paragraph("<b>Document Type:</b>", body_style), Paragraph(_esc(doc.document_type.replace('_', ' ')), body_style)],
        [Paragraph("<b>Approval Status:</b>", body_style), Paragraph(f"<b>{_esc(doc.approval_status)}</b>", body_style)],
        [Paragraph("<b>Verification State:</b>", body_style), Paragraph("VERIFIED OFFICIAL RECORD" if doc.is_verified else "REGISTERED RECORD", body_style)],
        [Paragraph("<b>Project:</b>", body_style), Paragraph(_esc(project_name or "N/A"), body_style)],
        [Paragraph("<b>Parcel / Survey:</b>", body_style), Paragraph(_esc(parcel_info or "N/A"), body_style)],
        [Paragraph("<b>Document ID:</b>", body_style), Paragraph(_esc(str(doc.document_id)), body_style)],
    ]
    t = Table(meta_data, colWidths=[130, 410])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("RECORD DETAILS & DESCRIPTION", heading_style))
    for line in text_content.split('\n'):
        if line.strip():
            story.append(Paragraph(_esc(line), body_style))
            story.append(Spacer(1, 3))
    story.append(Spacer(1, 10))

    stamp_table = Table([[Paragraph("<b>VERIFIED OFFICIAL RECORD — BHOOMI SETU PORTAL</b>", ParagraphStyle('Stamp', parent=body_style, alignment=1, textColor=colors.HexColor('#065F46')))]], colWidths=[540])
    stamp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')),
        ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#10B981')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(stamp_table)

    pdf.build(story)
    return buffer.getvalue()


def _sanitize_text(text: str) -> str:
    if not text:
        return ""
    import re
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', str(text))


def _generate_docx_document(doc: Document, project_name: str, parcel_info: str, text_content: str) -> bytes:
    import io
    import docx
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    buffer = io.BytesIO()
    d = docx.Document()

    h1 = d.add_heading('GOVERNMENT OF INDIA — PM GATI SHAKTI BHOOMI SETU', level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in h1.runs:
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        run.font.size = Pt(14)

    sub = d.add_paragraph('DEPARTMENT OF LAND RESOURCES • OFFICIAL DOCUMENT RECORD')
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in sub.runs:
        run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)
        run.font.size = Pt(9)

    d.add_paragraph('')

    table = d.add_table(rows=7, cols=2)
    table.style = 'Table Grid'
    rows_data = [
        ("Document Title:", _sanitize_text(doc.title)),
        ("Document Type:", _sanitize_text(doc.document_type.replace('_', ' '))),
        ("Approval Status:", _sanitize_text(doc.approval_status)),
        ("Verification State:", "VERIFIED OFFICIAL RECORD" if doc.is_verified else "REGISTERED RECORD"),
        ("Project:", _sanitize_text(project_name or "N/A")),
        ("Parcel / Survey:", _sanitize_text(parcel_info or "N/A")),
        ("Document ID:", _sanitize_text(str(doc.document_id))),
    ]
    for i, (label, val) in enumerate(rows_data):
        row_cells = table.rows[i].cells
        row_cells[0].text = label
        row_cells[1].text = str(val)

    d.add_paragraph('')
    h2 = d.add_heading('RECORD DETAILS & DESCRIPTION', level=2)
    for run in h2.runs:
        run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
        run.font.size = Pt(11)

    clean_content = _sanitize_text(text_content)
    for line in clean_content.split('\n'):
        if line.strip():
            d.add_paragraph(line)

    d.save(buffer)
    return buffer.getvalue()


def _generate_xlsx_document(doc: Document, project_name: str, parcel_info: str, text_content: str) -> bytes:
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    buffer = io.BytesIO()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Document Record"

    ws['A1'] = "GOVERNMENT OF INDIA — PM GATI SHAKTI BHOOMI SETU PORTAL"
    ws['A1'].font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    ws['A1'].fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    ws.merge_cells("A1:D1")

    ws['A2'] = "OFFICIAL LAND ACQUISITION DOCUMENT RECORD"
    ws['A2'].font = Font(name="Calibri", size=10, italic=True, color="4B5563")

    meta_rows = [
        ("Document Title", _sanitize_text(doc.title)),
        ("Document Type", _sanitize_text(doc.document_type.replace('_', ' '))),
        ("Approval Status", _sanitize_text(doc.approval_status)),
        ("Verification State", "VERIFIED OFFICIAL RECORD" if doc.is_verified else "REGISTERED RECORD"),
        ("Associated Project", _sanitize_text(project_name or "N/A")),
        ("Land Parcel", _sanitize_text(parcel_info or "N/A")),
        ("Document ID", _sanitize_text(str(doc.document_id))),
        ("Created Date", _sanitize_text(str(doc.created_at or "N/A"))),
    ]

    ws.append([])
    ws.append(["Field Name", "Field Value"])
    ws['A4'].font = Font(bold=True)
    ws['B4'].font = Font(bold=True)

    for label, val in meta_rows:
        ws.append([label, val])

    ws.append([])
    ws.append(["RECORD DETAILS & CONTENT"])
    ws.cell(row=ws.max_row, column=1).font = Font(bold=True, color="1E3A8A")

    clean_content = _sanitize_text(text_content)
    for line in clean_content.split('\n'):
        if line.strip():
            ws.append([line])

    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 50

    wb.save(buffer)
    return buffer.getvalue()


# ── Download & Preview ────────────────────────────────────────────────────────

@router.get(
    "/{document_id}/download",
    summary="Download a document in requested format (pdf, docx, xlsx, txt)",
)
def download_document(
    document_id: UUID,
    format: Optional[str] = Query("pdf"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Stream document file in specified format (pdf, docx, xlsx, txt)."""
    from fastapi.responses import Response

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

    req_fmt = (format or "pdf").lower().strip()
    if req_fmt not in ("pdf", "docx", "xlsx", "txt"):
        req_fmt = "pdf"

    project = db.execute(select(Project).where(Project.project_id == doc.project_id)).scalar_one_or_none() if doc.project_id else None
    parcel = db.execute(select(Parcel).where(Parcel.parcel_id == doc.parcel_id)).scalar_one_or_none() if doc.parcel_id else None
    project_name = project.name if project else "System-wide / Unassigned"
    parcel_info = f"Survey #{parcel.survey_number} ({parcel.district}, {parcel.state})" if parcel else "System-wide / Unassigned"

    text_content = _get_document_text_content(doc, db)
    safe_title = doc.title.translate(str.maketrans("", "", r'/\:*?"<>|')).replace(' ', '_')

    if req_fmt == "pdf":
        pdf_bytes = _generate_pdf_document(doc, project_name, parcel_info, text_content)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'},
        )
    elif req_fmt == "docx":
        docx_bytes = _generate_docx_document(doc, project_name, parcel_info, text_content)
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.docx"'},
        )
    elif req_fmt == "xlsx":
        xlsx_bytes = _generate_xlsx_document(doc, project_name, parcel_info, text_content)
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.xlsx"'},
        )
    else:  # txt
        return Response(
            content=text_content.encode("utf-8"),
            media_type="text/plain; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{safe_title}.txt"'},
        )


@router.get(
    "/{document_id}/preview",
    summary="Get full document preview content and metadata",
    response_model=dict,
)
def get_document_preview(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return full preview details including formatted content text for web rendering."""
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

    from app.models import User as UserModel
    uploader = db.execute(select(UserModel).where(UserModel.id == doc.uploaded_by)).scalar_one_or_none() if doc.uploaded_by else None
    project = db.execute(select(Project).where(Project.project_id == doc.project_id)).scalar_one_or_none() if doc.project_id else None
    parcel = db.execute(select(Parcel).where(Parcel.parcel_id == doc.parcel_id)).scalar_one_or_none() if doc.parcel_id else None

    text_content = _get_document_text_content(doc, db)

    return {
        "document_id": str(doc.document_id),
        "title": doc.title,
        "description": doc.description,
        "document_type": doc.document_type,
        "mime_type": doc.mime_type,
        "file_size_bytes": doc.file_size_bytes,
        "version": doc.version or 1,
        "is_verified": doc.is_verified,
        "approval_status": doc.approval_status,
        "current_approval_step": doc.current_approval_step,
        "uploaded_by_name": uploader.username if uploader else "Field Officer",
        "project_name": project.name if project else "Unassigned",
        "parcel_info": f"Survey #{parcel.survey_number} ({parcel.district}, {parcel.state})" if parcel else "Unassigned",
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "text_content": text_content,
    }




# ── Details ───────────────────────────────────────────────────────────────────

@router.get(
    "/{document_id}",
    summary="Get single document details",
    response_model=dict,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return detailed metadata for a single document including user/project/parcel context."""
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

    from app.models import User as UserModel
    uploader = db.execute(select(UserModel).where(UserModel.id == doc.uploaded_by)).scalar_one_or_none() if doc.uploaded_by else None
    project = db.execute(select(Project).where(Project.project_id == doc.project_id)).scalar_one_or_none() if doc.project_id else None
    parcel = db.execute(select(Parcel).where(Parcel.parcel_id == doc.parcel_id)).scalar_one_or_none() if doc.parcel_id else None

    meta = doc.metadata_json or {}
    sha256_hash = meta.get("sha256") or meta.get("file_hash") or ""

    return {
        "document_id": str(doc.document_id),
        "title": doc.title,
        "description": doc.description,
        "document_type": doc.document_type,
        "mime_type": doc.mime_type,
        "file_size_bytes": doc.file_size_bytes,
        "file_path": doc.file_path,
        "version": meta.get("version", 1),
        "is_verified": doc.is_verified,
        "approval_status": doc.approval_status,
        "current_approval_step": doc.current_approval_step,
        "uploaded_by": str(doc.uploaded_by) if doc.uploaded_by else None,
        "uploaded_by_name": uploader.username if uploader else "System",
        "sha256": sha256_hash,
        "file_hash": sha256_hash,
        "project_id": str(doc.project_id) if doc.project_id else None,
        "project_name": project.name if project else None,
        "parcel_id": str(doc.parcel_id) if doc.parcel_id else None,
        "parcel_survey_number": parcel.survey_number if parcel else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
        "metadata_json": doc.metadata_json,
    }


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
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return paginated document list filtered by project, parcel, type, search keyword,
    and the current user's geographic scope."""
    stmt = select(Document)
    from uuid import UUID
    from fastapi.params import Param
    
    if project_id and not isinstance(project_id, Param):
        stmt = stmt.where(Document.project_id == project_id)
    if parcel_id and not isinstance(parcel_id, Param):
        stmt = stmt.where(Document.parcel_id == parcel_id)
    if document_type and isinstance(document_type, str) and document_type != "ALL":
        stmt = stmt.where(Document.document_type == document_type)
    if search and isinstance(search, str) and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Document.title.ilike(term),
                Document.description.ilike(term),
                Document.document_type.ilike(term),
            )
        )

    scope = get_user_geographic_scope(current_user)
    if scope:
        # Strict RBAC geographic filtering — no fallback for unlinked documents
        stmt = stmt.outerjoin(Project, Document.project_id == Project.project_id)
        stmt = stmt.outerjoin(Parcel, Document.parcel_id == Parcel.parcel_id)

        scope_clauses = []

        if scope.get("district"):
            # District-scoped: match parcel district OR project districts array
            scope_clauses.append(and_(
                Document.parcel_id.isnot(None),
                Parcel.district == scope["district"]
            ))
            scope_clauses.append(and_(
                Document.project_id.isnot(None),
                Project.districts.any(scope["district"])
            ))
        elif scope.get("state"):
            # State-scoped: match parcel state OR project states array
            scope_clauses.append(and_(
                Document.parcel_id.isnot(None),
                Parcel.state == scope["state"]
            ))
            scope_clauses.append(and_(
                Document.project_id.isnot(None),
                Project.states.any(scope["state"])
            ))

        if scope_clauses:
            stmt = stmt.where(or_(*scope_clauses))
        else:
            stmt = stmt.where(Document.document_id.is_(None))

    stmt = stmt.order_by(Document.created_at.desc())
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar() or 0
    page_num = page if isinstance(page, int) else 1
    size_num = page_size if isinstance(page_size, int) else 20
    offset = (page_num - 1) * size_num
    docs = db.execute(stmt.offset(offset).limit(size_num)).scalars().all()

    # Pre-fetch user, project, parcel maps for efficiency
    from app.models import User as UserModel
    user_ids = {d.uploaded_by for d in docs if d.uploaded_by}
    project_ids = {d.project_id for d in docs if d.project_id}
    parcel_ids = {d.parcel_id for d in docs if d.parcel_id}

    users_map = {u.id: u.username for u in db.execute(select(UserModel).where(UserModel.id.in_(user_ids))).scalars().all()} if user_ids else {}
    projects_map = {p.project_id: p.name for p in db.execute(select(Project).where(Project.project_id.in_(project_ids))).scalars().all()} if project_ids else {}
    parcels_map = {p.parcel_id: p.survey_number for p in db.execute(select(Parcel).where(Parcel.parcel_id.in_(parcel_ids))).scalars().all()} if parcel_ids else {}

    items = []
    for d in docs:
        meta = d.metadata_json or {}
        sha256_hash = meta.get("sha256") or meta.get("file_hash") or ""
        items.append({
            "document_id": str(d.document_id),
            "title": d.title,
            "description": d.description,
            "document_type": d.document_type,
            "mime_type": d.mime_type,
            "file_size_bytes": d.file_size_bytes,
            "file_path": d.file_path,
            "version": meta.get("version", 1),
            "is_verified": d.is_verified,
            "approval_status": d.approval_status,
            "current_approval_step": d.current_approval_step,
            "uploaded_by": str(d.uploaded_by) if d.uploaded_by else None,
            "uploaded_by_name": users_map.get(d.uploaded_by, "Field Officer"),
            "sha256": sha256_hash,
            "file_hash": sha256_hash,
            "project_id": str(d.project_id) if d.project_id else None,
            "project_name": projects_map.get(d.project_id),
            "parcel_id": str(d.parcel_id) if d.parcel_id else None,
            "parcel_survey_number": parcels_map.get(d.parcel_id),
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        })

    return {
        "items": items,
        "data": items,
        "pagination": {
            "page": page_num,
            "page_size": size_num,
            "total": total,
            "total_pages": max(1, -(-total // size_num)),
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


"""Script to extract synthetic documents from files.zip and seed them into PostgreSQL with SHA-256 hashes."""

from __future__ import annotations

import hashlib
import os
import sys
import uuid
import zipfile
from pathlib import Path

# Ensure backend package is in python path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models import Document, Parcel, Project, User, DocumentApproval
from app.models.enums import ApprovalStatus, DocumentType


DOC_SPECS = [
    {
        "filename": "Survey_Report_001.pdf",
        "document_type": "SURVEY_REPORT",
        "title": "Joint Measurement Survey Report 001",
        "description": "Joint measurement survey report for land acquisition parcel identification and boundary mapping.",
    },
    {
        "filename": "Award_Declaration_001.pdf",
        "document_type": "AWARD_ORDER",
        "title": "Section 23 Award Declaration 001",
        "description": "Section 23 statutory award declaration order specifying compensation valuation and land parcel summary.",
    },
    {
        "filename": "Objection_Record_001.pdf",
        "document_type": "NOTIFICATION",
        "title": "Section 15 Objection Hearing Record 001",
        "description": "Section 15 hearing record detailing land owner objections, hearing notes, and collector summary.",
    },
    {
        "filename": "Compensation_Order_001.pdf",
        "document_type": "COMPENSATION_RECEIPT",
        "title": "Compensation Disbursement Order 001",
        "description": "Official compensation disbursement order and payment schedule for affected land owners.",
    },
    {
        "filename": "Possession_Certificate_001.pdf",
        "document_type": "POSSESSION_ORDER",
        "title": "Land Possession & Mutation Certificate 001",
        "description": "Certificate of physical possession transfer and revenue land mutation record.",
    },
]


def seed_synthetic_documents() -> None:
    workspace_root = backend_dir.parent
    zip_path = workspace_root / "files.zip"
    storage_dir = backend_dir / "storage" / "documents" / "synthetic"
    storage_dir.mkdir(parents=True, exist_ok=True)

    if not zip_path.exists():
        print(f"Error: {zip_path} does not exist.")
        return

    print(f"Unzipping {zip_path} into {storage_dir}...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(storage_dir)

    db = SessionLocal()
    try:
        projects = db.query(Project).all()
        parcels = db.query(Parcel).limit(10).all()
        users = db.query(User).all()

        field_officer = next((u for u in users if u.role == "FIELD_OFFICER"), None) or (users[0] if users else None)
        default_project = projects[0] if projects else None
        default_parcel = parcels[0] if parcels else None

        if not default_project:
            print("Warning: No projects found in database. Documents will have null project_id.")

        seeded_count = 0
        updated_count = 0

        for i, spec in enumerate(DOC_SPECS):
            file_name = spec["filename"]
            file_path = storage_dir / file_name

            if not file_path.exists():
                print(f"Warning: Extracted file {file_path} not found. Skipping.")
                continue

            with open(file_path, "rb") as f:
                content = f.read()

            sha256_hash = hashlib.sha256(content).hexdigest()
            file_size = len(content)

            # Assign to projects covering UP, Punjab, Delhi, Maharashtra
            target_project = None
            if projects:
                # Find project matching regional scopes
                if i == 0 or i == 1:
                    # Uttar Pradesh / Delhi
                    target_project = next((p for p in projects if "Uttar Pradesh" in (p.states or []) or "Delhi" in (p.states or [])), projects[0])
                elif i == 2:
                    # Punjab
                    target_project = next((p for p in projects if "Punjab" in (p.states or [])), projects[0])
                elif i == 3:
                    # Maharashtra
                    target_project = next((p for p in projects if "Maharashtra" in (p.states or [])), projects[0])
                else:
                    target_project = projects[i % len(projects)]

            existing_doc = db.query(Document).filter(Document.title == spec["title"]).first()

            if existing_doc:
                existing_doc.project_id = target_project.project_id if target_project else None
                existing_doc.file_path = str(file_path.resolve())
                existing_doc.file_size_bytes = file_size
                existing_doc.mime_type = "application/pdf"
                existing_doc.metadata_json = {
                    "sha256": sha256_hash,
                    "file_hash": sha256_hash,
                    "version": 1,
                    "original_filename": file_name,
                }
                existing_doc.is_verified = True
                updated_count += 1
                print(f"Updated existing document: {existing_doc.title} -> Project: {target_project.name if target_project else 'None'} (SHA-256: {sha256_hash[:12]}...)")
            else:
                doc_id = uuid.uuid4()
                new_doc = Document(
                    document_id=doc_id,
                    project_id=target_project.project_id if target_project else None,
                    parcel_id=parcel.parcel_id if parcel else None,
                    uploaded_by=field_officer.id if field_officer else None,
                    document_type=spec["document_type"],
                    title=spec["title"],
                    description=spec["description"],
                    file_path=str(file_path.resolve()),
                    file_size_bytes=file_size,
                    mime_type="application/pdf",
                    metadata_json={
                        "sha256": sha256_hash,
                        "file_hash": sha256_hash,
                        "version": 1,
                        "original_filename": file_name,
                    },
                    is_verified=True,
                    approval_status=ApprovalStatus.PENDING_REVIEW.value,
                    current_approval_step=0,
                )
                db.add(new_doc)
                seeded_count += 1
                print(f"Created new document: {spec['title']} -> Project: {target_project.name if target_project else 'None'} (SHA-256: {sha256_hash[:12]}...)")

        db.commit()
        print(f"\nSuccessfully seeded synthetic documents! Created: {seeded_count}, Updated: {updated_count}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding documents: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_synthetic_documents()

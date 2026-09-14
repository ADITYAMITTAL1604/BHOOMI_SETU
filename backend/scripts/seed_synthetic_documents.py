"""Script to extract synthetic documents from files.zip and seed them into PostgreSQL with SHA-256 hashes.

Ensures each document links to a parcel that geographically matches the
target project's state/district, and sets uploaded_by to a user whose
scope matches that geography (RBAC-correct seeding).
"""

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

# Each doc spec now includes target_state to match against a project + parcel
DOC_SPECS = [
    {
        "filename": "Survey_Report_001.pdf",
        "sample_txt": "Survey_Report_001.txt",
        "document_type": "SURVEY_REPORT",
        "title": "Joint Measurement Survey Report 001",
        "description": "Joint measurement survey report for land acquisition parcel identification and boundary mapping.",
        "target_states": ["Uttar Pradesh", "Delhi"],
    },
    {
        "filename": "Award_Declaration_001.pdf",
        "sample_txt": "Award_Declaration_001.txt",
        "document_type": "AWARD_ORDER",
        "title": "Section 23 Award Declaration 001",
        "description": "Section 23 statutory award declaration order specifying compensation valuation and land parcel summary.",
        "target_states": ["Uttar Pradesh", "Delhi"],
    },
    {
        "filename": "Objection_Record_001.pdf",
        "sample_txt": "Objection_Record_001.txt",
        "document_type": "NOTIFICATION",
        "title": "Section 15 Objection Hearing Record 001",
        "description": "Section 15 hearing record detailing land owner objections, hearing notes, and collector summary.",
        "target_states": ["Punjab"],
    },
    {
        "filename": "Compensation_Order_001.pdf",
        "sample_txt": "Compensation_Order_001.txt",
        "document_type": "COMPENSATION_RECEIPT",
        "title": "Compensation Disbursement Order 001",
        "description": "Official compensation disbursement order and payment schedule for affected land owners.",
        "target_states": ["Maharashtra"],
    },
    {
        "filename": "Possession_Certificate_001.pdf",
        "sample_txt": "Possession_Certificate_001.txt",
        "document_type": "POSSESSION_ORDER",
        "title": "Land Possession & Mutation Certificate 001",
        "description": "Certificate of physical possession transfer and revenue land mutation record.",
        "target_states": ["Rajasthan"],
    },
]


def _find_project_for_states(projects, target_states):
    """Find a project whose states overlap with target_states."""
    for p in projects:
        proj_states = p.states or []
        if any(ts in proj_states for ts in target_states):
            return p
    return projects[0] if projects else None


def _find_or_create_parcel(db, project, target_states):
    """Find an existing parcel in the project's state, or create one."""
    if not project:
        return None

    proj_states = project.states or []
    proj_districts = project.districts or []

    # Pick the first state from target that matches the project
    target_state = None
    for ts in target_states:
        if ts in proj_states:
            target_state = ts
            break
    if not target_state and proj_states:
        target_state = proj_states[0]

    target_district = proj_districts[0] if proj_districts else None

    # Check if a parcel already exists in this state+district for this project
    existing = db.query(Parcel).filter(
        Parcel.project_id == project.project_id,
        Parcel.state == target_state,
    ).first()

    if existing:
        return existing

    # Check any parcel with matching state (across all projects)
    existing = db.query(Parcel).filter(
        Parcel.state == target_state,
    ).first()

    if existing:
        return existing

    # Create a new parcel for this state/district
    parcel = Parcel(
        parcel_id=uuid.uuid4(),
        project_id=project.project_id,
        survey_number=f"Khasra {target_state[:3].upper()}/1",
        state=target_state,
        district=target_district,
        area_acres=2.5,
        status="ACQUIRED",
    )
    db.add(parcel)
    db.flush()  # Get the ID without committing
    print(f"  Created new parcel: state={target_state}, district={target_district}, project={project.name}")
    return parcel


def _find_uploader_for_state(users, target_state):
    """Find a FIELD_OFFICER whose state_scope matches the target state."""
    # First try exact state match with FIELD_OFFICER role
    for u in users:
        if u.role == "FIELD_OFFICER" and u.state_scope == target_state:
            return u
    # Fallback: any user with matching state_scope
    for u in users:
        if u.state_scope == target_state:
            return u
    # Final fallback: any field officer
    for u in users:
        if u.role == "FIELD_OFFICER":
            return u
    return users[0] if users else None


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
        users = db.query(User).all()

        if not projects:
            print("Warning: No projects found in database. Documents will have null project_id.")

        seeded_count = 0
        updated_count = 0

        for spec in DOC_SPECS:
            file_name = spec["filename"]
            file_path = storage_dir / file_name
            target_states = spec["target_states"]

            if not file_path.exists():
                print(f"Warning: Extracted file {file_path} not found. Skipping.")
                continue

            with open(file_path, "rb") as f:
                content = f.read()

            # Read matching .txt sample document for full in-browser preview content
            sample_txt_path = workspace_root / "sih-upgrade-context" / "sample_documents" / spec.get("sample_txt", "")
            sample_text = None
            if sample_txt_path.exists():
                try:
                    sample_text = sample_txt_path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    pass

            sha256_hash = hashlib.sha256(content).hexdigest()
            file_size = len(content)

            # Find project matching the target states
            target_project = _find_project_for_states(projects, target_states)

            # Find or create a geographically-correct parcel
            target_parcel = _find_or_create_parcel(db, target_project, target_states)

            # Find the correct uploader for this state
            uploader = _find_uploader_for_state(users, target_states[0])

            meta = {
                "sha256": sha256_hash,
                "file_hash": sha256_hash,
                "version": 1,
                "original_filename": file_name,
            }
            if sample_text:
                meta["content_text"] = sample_text

            existing_doc = db.query(Document).filter(Document.title == spec["title"]).first()

            if existing_doc:
                existing_doc.project_id = target_project.project_id if target_project else None
                existing_doc.parcel_id = target_parcel.parcel_id if target_parcel else None
                existing_doc.uploaded_by = uploader.id if uploader else None
                existing_doc.file_path = str(file_path.resolve())
                existing_doc.file_size_bytes = file_size
                existing_doc.mime_type = "application/pdf"
                existing_doc.metadata_json = meta
                existing_doc.is_verified = True
                updated_count += 1
                parcel_info = f"state={target_parcel.state}, district={target_parcel.district}" if target_parcel else "no parcel"
                uploader_info = f"{uploader.username} ({uploader.state_scope})" if uploader else "None"
                print(f"Updated: {existing_doc.title}")
                print(f"  -> Project: {target_project.name if target_project else 'None'}")
                print(f"  -> Parcel: {parcel_info}")
                print(f"  -> Uploader: {uploader_info}")
                print(f"  -> Content Text Loaded: {len(sample_text or '')} chars")
            else:
                doc_id = uuid.uuid4()
                new_doc = Document(
                    document_id=doc_id,
                    project_id=target_project.project_id if target_project else None,
                    parcel_id=target_parcel.parcel_id if target_parcel else None,
                    uploaded_by=uploader.id if uploader else None,
                    document_type=spec["document_type"],
                    title=spec["title"],
                    description=spec["description"],
                    file_path=str(file_path.resolve()),
                    file_size_bytes=file_size,
                    mime_type="application/pdf",
                    metadata_json=meta,
                    is_verified=True,
                    approval_status=ApprovalStatus.PENDING_REVIEW.value,
                    current_approval_step=0,
                )
                db.add(new_doc)
                seeded_count += 1
                parcel_info = f"state={target_parcel.state}, district={target_parcel.district}" if target_parcel else "no parcel"
                uploader_info = f"{uploader.username} ({uploader.state_scope})" if uploader else "None"
                print(f"Created: {spec['title']}")
                print(f"  -> Project: {target_project.name if target_project else 'None'}")
                print(f"  -> Parcel: {parcel_info}")
                print(f"  -> Uploader: {uploader_info}")

        db.commit()
        print(f"\nSeed complete! Created: {seeded_count}, Updated: {updated_count}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding documents: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_synthetic_documents()

"""Tests for stage transition service, SLA breach logic, and audit logging."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import ParcelStatus, ProjectStatus, StageName, StageStatus
from app.models.project import Project
from app.models.parcel import Parcel
from app.models.stage import AcquisitionStage
from app.models.audit_log import AuditLog
from app.services.transition import STAGE_ORDER


def test_stage_transition_valid_flow(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
):
    """Transitioning to the next ordered stage succeeds and records audit log."""
    proj = Project(
        project_id=uuid.uuid4(),
        name="Workflow Test Corridor",
        type="Highway",
        states=["Maharashtra"],
        districts=["Pune"],
        land_required_ha=50.0,
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    db_session.commit()

    parcel = Parcel(
        parcel_id=uuid.uuid4(),
        project_id=proj.project_id,
        survey_number="WF-01",
        area_ha=1.0,
        current_stage=StageName.PROPOSAL.value,
        status=ParcelStatus.IN_PROGRESS.value,
        village="Wagholi",
        district="Pune",
        state="Maharashtra",
    )
    db_session.add(parcel)
    db_session.commit()

    # Seed all stages for this parcel
    today = date.today()
    for order, s_enum in enumerate(STAGE_ORDER, start=1):
        stg = AcquisitionStage(
            stage_id=uuid.uuid4(),
            parcel_id=parcel.parcel_id,
            stage_name=s_enum.value,
            stage_order=order,
            status=StageStatus.IN_PROGRESS.value if order == 1 else StageStatus.NOT_STARTED.value,
            start_date=today - timedelta(days=10) if order == 1 else None,
            target_date=today + timedelta(days=20) if order == 1 else None,
        )
        db_session.add(stg)
    db_session.commit()

    # Progress to next stage: IDENTIFICATION
    trans_payload = {
        "target_stage": StageName.IDENTIFICATION.value,
        "remarks": "Completed initial proposal review",
    }
    res = client.post(
        f"/api/v1/parcels/{parcel.parcel_id}/transition",
        json=trans_payload,
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_200_OK

    db_session.refresh(parcel)
    assert parcel.current_stage == StageName.IDENTIFICATION.value

    # Verify audit log was written
    audit = db_session.query(AuditLog).filter(
        AuditLog.entity_id == parcel.parcel_id,
        AuditLog.action == "STAGE_TRANSITION",
    ).first()
    assert audit is not None
    assert audit.new_values.get("stage") == StageName.IDENTIFICATION.value


def test_stage_transition_invalid_skip(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
):
    """Attempting to jump or skip intermediate workflow stages must be rejected."""
    proj = Project(
        project_id=uuid.uuid4(),
        name="Invalid Skip Corridor",
        type="Highway",
        states=["Maharashtra"],
        districts=["Pune"],
        land_required_ha=50.0,
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    db_session.commit()

    parcel = Parcel(
        parcel_id=uuid.uuid4(),
        project_id=proj.project_id,
        survey_number="WF-02",
        area_ha=1.0,
        current_stage=StageName.PROPOSAL.value,
        status=ParcelStatus.IN_PROGRESS.value,
        village="Wagholi",
        district="Pune",
        state="Maharashtra",
    )
    db_session.add(parcel)
    db_session.commit()

    # Try skipping directly to POSSESSION (illegal transition)
    trans_payload = {
        "target_stage": StageName.POSSESSION.value,
        "remarks": "Illegal skip attempt",
    }
    res = client.post(
        f"/api/v1/parcels/{parcel.parcel_id}/transition",
        json=trans_payload,
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "is not allowed" in res.json()["detail"]

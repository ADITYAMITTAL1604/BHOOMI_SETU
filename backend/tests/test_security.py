"""Security tests for RBAC, Geographic Scope (BOLA), and Mass Assignment protection."""

from __future__ import annotations

import uuid
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import ProjectStatus
from app.models.project import Project
from app.models.parcel import Parcel
from app.models.user import User


def test_unauthenticated_request_rejected(client: TestClient):
    """Endpoints require valid authentication headers."""
    res = client.get("/api/v1/projects")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


def test_rbac_field_officer_cannot_create_project(client: TestClient, field_officer_headers: dict[str, str]):
    """BFLA: FIELD_OFFICER role cannot create projects."""
    payload = {
        "name": "Unauthorized Project Creation",
        "type": "Highway",
        "states": ["Maharashtra"],
        "districts": ["Pune"],
        "land_required_ha": 50.0,
        "land_acquired_ha": 0.0,
        "status": "PLANNING",
    }
    res = client.post("/api/v1/projects", json=payload, headers=field_officer_headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_create_project(client: TestClient, admin_headers: dict[str, str]):
    """Admin role has privilege to create projects."""
    payload = {
        "name": f"Admin Highway Project {uuid.uuid4().hex[:6]}",
        "type": "Highway",
        "states": ["Maharashtra"],
        "districts": ["Pune"],
        "land_required_ha": 75.0,
        "land_acquired_ha": 10.0,
        "status": "PLANNING",
    }
    res = client.post("/api/v1/projects", json=payload, headers=admin_headers)
    assert res.status_code == status.HTTP_201_CREATED
    assert res.json()["name"] == payload["name"]


def test_geographic_scope_state_user(client: TestClient, state_user_headers: dict[str, str], db_session: Session):
    """BOLA: State user from Maharashtra only receives projects in Maharashtra."""
    # Ensure there is a project in Maharashtra and one in Uttar Pradesh
    mh_proj = Project(
        project_id=uuid.uuid4(),
        name="MH Scoped Highway",
        type="Highway",
        states=["Maharashtra"],
        districts=["Pune"],
        land_required_ha=100.0,
        status=ProjectStatus.ACTIVE.value,
    )
    up_proj = Project(
        project_id=uuid.uuid4(),
        name="UP Scoped Highway",
        type="Highway",
        states=["Uttar Pradesh"],
        districts=["Moradabad"],
        land_required_ha=100.0,
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(mh_proj)
    db_session.add(up_proj)
    db_session.commit()

    res = client.get("/api/v1/projects", headers=state_user_headers)
    assert res.status_code == status.HTTP_200_OK
    items = res.json()["items"]
    # All returned projects must contain Maharashtra in states
    for p in items:
        assert "Maharashtra" in p["states"], f"Project {p['name']} outside Maharashtra leaked to state user!"


def test_mass_assignment_protection_on_parcels(
    client: TestClient,
    field_officer_headers: dict[str, str],
    state_user_headers: dict[str, str],
    admin_headers: dict[str, str],
    db_session: Session,
):
    """Field officer cannot overwrite protected parcel workflow status or risk_score."""
    proj = Project(
        project_id=uuid.uuid4(),
        name="Parcel Security Test Corridor",
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
        survey_number="SEC-101/A",
        area_ha=2.5,
        owner_name="Original Landowner",
        current_stage="SURVEY",
        status="IN_PROGRESS",
        risk_score=25.0,
        village="Wagholi",
        district="Pune",
        state="Maharashtra",
    )
    db_session.add(parcel)
    db_session.commit()

    # 1. Field officer cannot update parcel directly (requires district or above)
    fo_res = client.put(
        f"/api/v1/parcels/{parcel.parcel_id}",
        json={"owner_name": "Field Attempt"},
        headers=field_officer_headers,
    )
    assert fo_res.status_code == status.HTTP_403_FORBIDDEN

    # 2. Non-admin user (e.g. State user) attempting to tamper with protected workflow/risk fields gets 403
    tampered_payload = {
        "owner_name": "Updated Landowner",
        "current_stage": "CLOSURE",
        "status": "COMPLETED",
        "risk_score": 0.0,
    }
    state_tamper_res = client.put(
        f"/api/v1/parcels/{parcel.parcel_id}",
        json=tampered_payload,
        headers=state_user_headers,
    )
    assert state_tamper_res.status_code == status.HTTP_403_FORBIDDEN
    assert "requires ADMIN privileges" in state_tamper_res.json()["detail"]

    # 3. Legitimate update without protected fields succeeds
    legit_payload = {
        "owner_name": "Legitimate Owner Update",
        "area_ha": 3.0,
    }
    legit_res = client.put(
        f"/api/v1/parcels/{parcel.parcel_id}",
        json=legit_payload,
        headers=state_user_headers,
    )
    assert legit_res.status_code == status.HTTP_200_OK

    db_session.refresh(parcel)
    assert parcel.owner_name == "Legitimate Owner Update"
    assert parcel.current_stage == "SURVEY"
    assert parcel.status == "IN_PROGRESS"
    assert parcel.risk_score == 25.0

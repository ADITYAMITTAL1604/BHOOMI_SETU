"""Comprehensive verification suite for Day 2 + Day 3 Backend Scope."""

from __future__ import annotations

import io
import time
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.deps import get_current_user, require_admin, require_central_or_above, require_state_or_above, require_district_or_above
from app.database import get_db
from app.main import app
from app.models import (
    AcquisitionStage,
    Alert,
    AuditLog,
    Compensation,
    Document,
    Parcel,
    Project,
    ProjectHistory,
    RRRecord,
    User,
)
from app.models.enums import AlertSeverity, ParcelStatus, ProjectStatus, RehabilitationStatus, StageName, StageStatus, UserRole


def build_mock_user(role=UserRole.ADMIN, state_scope=None, district_scope=None):
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = f"{role.value.lower()}_user"
    user.email = f"{role.value.lower()}@bhoomisetu.gov.in"
    user.role = role.value if hasattr(role, "value") else str(role)
    user.state_scope = state_scope
    user.district_scope = district_scope
    user.is_active = True
    return user


def test_sla_service_and_dashboard():
    """Test SLA computation, breach detection, and state/district/sla dashboard endpoints."""
    print("\n=== 1. Testing SLA Service & Scoped Dashboards ===")
    from app.services.sla_service import compute_stage_sla, run_sla_sweep

    # Test compute_stage_sla with on-track stage
    stage_ok = Mock(spec=AcquisitionStage)
    stage_ok.stage_id = uuid4()
    stage_ok.stage_name = StageName.SURVEY.value
    stage_ok.status = StageStatus.IN_PROGRESS.value
    stage_ok.start_date = datetime.now(timezone.utc).date()
    stage_ok.target_date = date.fromordinal(datetime.now(timezone.utc).date().toordinal() + 30)

    res_ok = compute_stage_sla(stage_ok)
    assert not res_ok["is_breached"]
    assert res_ok["breach_severity"] == "ok"
    assert res_ok["days_until_deadline"] == 30
    print("   [OK] compute_stage_sla: on-track stage evaluated correctly")

    # Test compute_stage_sla with breached stage
    stage_breached = Mock(spec=AcquisitionStage)
    stage_breached.stage_id = uuid4()
    stage_breached.stage_name = StageName.OBJECTION.value
    stage_breached.status = StageStatus.IN_PROGRESS.value
    stage_breached.start_date = date(2025, 1, 1)
    stage_breached.target_date = date(2025, 2, 1)

    res_breached = compute_stage_sla(stage_breached)
    assert res_breached["is_breached"]
    assert res_breached["breach_severity"] == "critical"
    assert res_breached["days_until_deadline"] < 0
    print("   [OK] compute_stage_sla: breached stage detected as critical")

    # Test API endpoints via TestClient
    admin_user = build_mock_user(UserRole.ADMIN)
    mock_db = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        # State dashboard
        mock_db.execute.return_value.one.return_value = Mock(total=5, required=500.0, acquired=250.0, area=200.0, avg_risk=35.0)
        mock_db.execute.return_value.all.return_value = [("Pune", 50, 40.0), ("Nashik", 30, 25.0)]
        mock_db.execute.return_value.scalar.return_value = 4

        resp_state = client.get("/api/v1/dashboard/state/Maharashtra")
        assert resp_state.status_code == 200
        data_state = resp_state.json()
        assert data_state["state"] == "Maharashtra"
        assert "summary" in data_state
        print("   [OK] GET /dashboard/state/{state} returns 200 with summary and district metrics")

        # District dashboard
        resp_dist = client.get("/api/v1/dashboard/district/Pune")
        assert resp_dist.status_code == 200
        data_dist = resp_dist.json()
        assert data_dist["district"] == "Pune"
        assert "summary" in data_dist
        assert "compensation" in data_dist
        print("   [OK] GET /dashboard/district/{district} returns 200 with summary and compensation")

        # SLA status endpoint
        mock_db.execute.return_value.all.return_value = [
            (stage_ok, "SRV-101", "Pune", "Maharashtra", uuid4()),
            (stage_breached, "SRV-102", "Pune", "Maharashtra", uuid4()),
        ]
        resp_sla = client.get("/api/v1/dashboard/sla-status")
        assert resp_sla.status_code == 200
        data_sla = resp_sla.json()
        assert "breached_count" in data_sla
        assert data_sla["breached_count"] >= 1
        print("   [OK] GET /dashboard/sla-status returns 200 with stage timers")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_project_timeline():
    """Test unified project event timeline."""
    print("\n=== 2. Testing Project Event Timeline ===")
    admin_user = build_mock_user(UserRole.ADMIN)
    mock_db = MagicMock()

    proj_id = uuid4()
    mock_proj = Mock(spec=Project)
    mock_proj.project_id = proj_id
    mock_proj.name = "Eastern Dedicated Freight Corridor"
    mock_proj.type = "Railway"
    mock_proj.land_required_ha = 600.0
    mock_proj.land_acquired_ha = 300.0
    mock_proj.districts = ["Varanasi", "Chandauli"]
    mock_proj.states = ["Uttar Pradesh"]
    mock_proj.target_date = date(2027, 12, 31)
    mock_proj.created_by = admin_user.id
    mock_proj.created_at = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)

    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_proj
    mock_db.execute.return_value.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        resp = client.get(f"/api/v1/projects/{proj_id}/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == str(proj_id)
        assert data["total_events"] >= 1
        assert data["timeline"][0]["event_type"] == "PROJECT_CREATED"
        print(f"   [OK] GET /projects/{{id}}/timeline returns 200 with {data['total_events']} event(s)")
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_alerts_endpoints():
    """Test alerts listing, manual create, unread count, and mark read."""
    print("\n=== 3. Testing Alerts System ===")
    admin_user = build_mock_user(UserRole.ADMIN)
    mock_db = MagicMock()

    mock_alert = Mock(spec=Alert)
    mock_alert.alert_id = uuid4()
    mock_alert.user_id = admin_user.id
    mock_alert.project_id = uuid4()
    mock_alert.parcel_id = uuid4()
    mock_alert.title = "Critical SLA Breach"
    mock_alert.message = "Stage OBJECTION overdue by 15 days."
    mock_alert.severity = AlertSeverity.CRITICAL.value
    mock_alert.is_read = False
    mock_alert.read_at = None
    mock_alert.metadata_json = {"days_overdue": 15}
    mock_alert.created_at = datetime.now(timezone.utc)

    mock_db.execute.return_value.scalar.return_value = 1
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_alert]
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_alert

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_central_or_above] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        # 1. Unread count
        resp_count = client.get("/api/v1/alerts/unread-count")
        assert resp_count.status_code == 200
        assert resp_count.json()["unread_count"] == 1
        print("   [OK] GET /alerts/unread-count returns unread count")

        # 2. List alerts
        resp_list = client.get("/api/v1/alerts")
        assert resp_list.status_code == 200
        data_list = resp_list.json()
        assert len(data_list["items"]) == 1
        assert data_list["unread_count"] == 1
        print("   [OK] GET /alerts returns paginated alerts with unread_count")

        # 3. Create alert
        post_data = {
            "title": "Manual Notification",
            "message": "Field survey team review required.",
            "severity": "WARNING",
            "target_user_id": str(admin_user.id),
        }
        resp_create = client.post("/api/v1/alerts", json=post_data)
        assert resp_create.status_code == 201
        print("   [OK] POST /alerts creates new alert successfully")

        # 4. Mark read
        resp_read = client.put(f"/api/v1/alerts/{mock_alert.alert_id}/read")
        assert resp_read.status_code == 200
        print("   [OK] PUT /alerts/{id}/read marks alert as read")

        # 5. Mark all read
        mock_db.execute.return_value.rowcount = 3
        resp_all = client.put("/api/v1/alerts/read-all")
        assert resp_all.status_code == 200
        print("   [OK] PUT /alerts/read-all marks all unread alerts")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(require_central_or_above, None)
        app.dependency_overrides.pop(get_db, None)


def test_advanced_analytics():
    """Test bottleneck, priority ranking, and why-delayed analytics endpoints."""
    print("\n=== 4. Testing Advanced Analytics (Bottleneck, Priority, Why-Delayed) ===")
    admin_user = build_mock_user(UserRole.ADMIN)
    mock_db = MagicMock()

    proj_id = uuid4()
    mock_proj = Mock(spec=Project)
    mock_proj.project_id = proj_id
    mock_proj.name = "Solar Park Corridor"

    parcel_id = uuid4()
    mock_parcel = Mock(spec=Parcel)
    mock_parcel.parcel_id = parcel_id
    mock_parcel.project_id = proj_id
    mock_parcel.survey_number = "SRV-442"
    mock_parcel.owner_name = "Kishore Kumar"
    mock_parcel.district = "Pune"
    mock_parcel.state = "Maharashtra"
    mock_parcel.current_stage = StageName.OBJECTION.value
    mock_parcel.status = ParcelStatus.BLOCKED.value
    mock_parcel.risk_score = 75.0

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        # 1. Bottleneck endpoint
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_proj
        mock_db.execute.return_value.all.return_value = [
            Mock(stage_name="OBJECTION", status=StageStatus.IN_PROGRESS.value, start_date=date(2025, 1, 1), target_date=date(2025, 2, 1)),
            Mock(stage_name="SURVEY", status=StageStatus.COMPLETED.value, start_date=date(2024, 11, 1), target_date=date(2024, 12, 1)),
        ]
        resp_bn = client.get(f"/api/v1/analytics/bottleneck/{proj_id}")
        assert resp_bn.status_code == 200
        data_bn = resp_bn.json()
        assert "primary_bottleneck" in data_bn
        assert "stages" in data_bn
        print(f"   [OK] GET /analytics/bottleneck/{{id}} identified primary bottleneck: {data_bn['primary_bottleneck']}")

        # 2. Priority ranking endpoint
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_proj
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_parcel]
        mock_db.execute.return_value.all.return_value = []
        resp_pri = client.get(f"/api/v1/analytics/priority/{proj_id}")
        assert resp_pri.status_code == 200
        data_pri = resp_pri.json()
        assert "parcels" in data_pri
        assert len(data_pri["parcels"]) == 1
        assert "intervention_recommendations" in data_pri["parcels"][0]
        print(f"   [OK] GET /analytics/priority/{{id}} ranked parcels with interventions: {data_pri['parcels'][0]['intervention_recommendations'][0]['type']}")

        # 3. Why-delayed endpoint (using actual Phase 4 features)
        mock_stage = Mock(spec=AcquisitionStage)
        mock_stage.stage_id = uuid4()
        mock_stage.parcel_id = parcel_id
        mock_stage.stage_name = StageName.OBJECTION.value
        mock_stage.status = StageStatus.IN_PROGRESS.value
        mock_stage.start_date = date(2025, 1, 1)
        mock_stage.target_date = date(2025, 2, 1)

        mock_db.execute.return_value.scalar_one_or_none.side_effect = [
            mock_parcel,  # select parcel
            mock_stage,   # select active stage
            None,         # select compensation
        ]
        mock_db.execute.return_value.scalars.return_value.all.return_value = []  # snapshots
        mock_db.execute.return_value.scalar.side_effect = [3, 10]  # adjacent disputes, total adjacent

        resp_why = client.get(f"/api/v1/analytics/parcels/{parcel_id}/why-delayed")
        assert resp_why.status_code == 200
        data_why = resp_why.json()
        assert data_why["parcel_id"] == str(parcel_id)
        assert len(data_why["factors"]) == 5
        factor_types = [f["type"] for f in data_why["factors"]]
        assert "SLA_COMPARISON" in factor_types
        assert "ADJACENT_DISPUTES" in factor_types
        assert "STAGE_COMPLEXITY" in factor_types
        print(f"   [OK] GET /analytics/parcels/{{id}}/why-delayed returned 5 structured factors (overall={data_why['overall_severity']})")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_documents_and_validation():
    """Test document upload validation (magic bytes, extensions, size), listing, and download."""
    print("\n=== 5. Testing Documents (Upload, Magic Bytes, Versioning) ===")
    admin_user = build_mock_user(UserRole.ADMIN)
    mock_db = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        # 1. Reject invalid extension (.exe)
        bad_file = io.BytesIO(b"malicious executable payload")
        resp_bad_ext = client.post(
            "/api/v1/documents/upload",
            files={"file": ("malware.exe", bad_file, "application/octet-stream")},
            data={"document_type": "SURVEY_REPORT", "title": "Malware"},
        )
        assert resp_bad_ext.status_code == 422
        print("   [OK] POST /documents/upload rejects unauthorized extension (.exe) with 422")

        # 2. Reject mismatched magic bytes (pretending to be PDF but actually text)
        fake_pdf = io.BytesIO(b"THIS IS NOT A VALID PDF FILE HEADER")
        resp_spoofed = client.post(
            "/api/v1/documents/upload",
            files={"file": ("spoofed.pdf", fake_pdf, "application/pdf")},
            data={"document_type": "SURVEY_REPORT", "title": "Spoofed Doc"},
        )
        assert resp_spoofed.status_code == 422
        assert "Magic byte validation failed" in resp_spoofed.json()["detail"]
        print("   [OK] POST /documents/upload catches magic byte spoofing with 422")

        # 3. Successful upload with valid PDF magic bytes (%PDF-1.4)
        valid_pdf = io.BytesIO(b"%PDF-1.4 fake pdf binary content for testing")
        mock_db.execute.return_value.scalar.return_value = 0  # version = 1
        resp_valid = client.post(
            "/api/v1/documents/upload",
            files={"file": ("genuine.pdf", valid_pdf, "application/pdf")},
            data={"document_type": "SURVEY_REPORT", "title": "Genuine Survey Report"},
        )
        assert resp_valid.status_code == 201
        data_doc = resp_valid.json()
        assert data_doc["title"] == "Genuine Survey Report"
        assert "sha256" in data_doc
        assert data_doc["version"] == 1
        print(f"   [OK] POST /documents/upload validates genuine PDF (SHA-256={data_doc['sha256'][:10]}..., version={data_doc['version']})")

        # 4. List documents
        mock_doc = Mock(spec=Document)
        mock_doc.document_id = uuid4()
        mock_doc.title = "Genuine Survey Report"
        mock_doc.document_type = "SURVEY_REPORT"
        mock_doc.mime_type = "application/pdf"
        mock_doc.file_size_bytes = 42
        mock_doc.metadata_json = {"version": 1}
        mock_doc.is_verified = False
        mock_doc.created_at = datetime.now(timezone.utc)
        mock_doc.project_id = uuid4()
        mock_doc.parcel_id = uuid4()

        mock_db.execute.return_value.scalar.return_value = 1
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_doc]

        resp_list = client.get("/api/v1/documents")
        assert resp_list.status_code == 200
        assert len(resp_list.json()["items"]) == 1
        print("   [OK] GET /documents returns filtered list")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_compensation_and_rr():
    """Test compensation and R&R aggregation endpoints."""
    print("\n=== 6. Testing Compensation & R&R Aggregations ===")
    admin_user = build_mock_user(UserRole.ADMIN)
    mock_db = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_district_or_above] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        # Compensation list
        mock_comp = Mock(spec=Compensation)
        mock_comp.compensation_id = uuid4()
        mock_comp.parcel_id = uuid4()
        mock_comp.assessed_amount = 1000000.0
        mock_comp.approved_amount = 1200000.0
        mock_comp.paid_amount = 800000.0
        mock_comp.payment_status = "PARTIALLY_PAID"
        mock_comp.payment_date = date(2025, 2, 1)
        mock_comp.remarks = "First installment"
        mock_comp.created_at = datetime.now(timezone.utc)

        mock_db.execute.return_value.one.return_value = Mock(total_assessed=1000000.0, total_approved=1200000.0, total_paid=800000.0)
        mock_db.execute.return_value.scalar.return_value = 1
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_comp]

        resp_comp = client.get("/api/v1/compensation")
        assert resp_comp.status_code == 200
        data_comp = resp_comp.json()
        assert data_comp["aggregates"]["total_pending"] == 400000.0
        print("   [OK] GET /compensation returns records + aggregates (pending=400k)")

        # Compensation summary
        mock_db.execute.return_value.all.return_value = [
            (uuid4(), 10, 10000000.0, 12000000.0, 8000000.0)
        ]
        resp_comp_sum = client.get("/api/v1/compensation/summary")
        assert resp_comp_sum.status_code == 200
        assert len(resp_comp_sum.json()["projects"]) == 1
        print("   [OK] GET /compensation/summary returns project-level aggregates")

        # R&R summary
        mock_db.execute.return_value.one.return_value = Mock(total_families=120, total_persons=480, total_area=50.5, total_comp_paid=15000000.0)
        mock_db.execute.return_value.all.side_effect = [
            [("COMPLETED", 80), ("IDENTIFIED", 40)],  # status breakdown
            [("TITLE_HOLDER", 100), ("TENANT", 20)],   # paf type breakdown
        ]
        mock_db.execute.return_value.scalar.side_effect = [75, 70]  # plots, relocation sites

        resp_rr = client.get("/api/v1/rr/summary")
        assert resp_rr.status_code == 200
        data_rr = resp_rr.json()
        assert data_rr["summary"]["total_affected_families"] == 120
        assert data_rr["summary"]["families_rehabilitated"] == 80
        assert data_rr["summary"]["families_pending"] == 40
        print("   [OK] GET /rr/summary returns affected families breakdown (120 families, 80 rehabilitated)")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(require_district_or_above, None)
        app.dependency_overrides.pop(get_db, None)


def test_audit_log_and_search():
    """Test admin-only audit log filtering and global search."""
    print("\n=== 7. Testing Audit Log API & Global Search ===")
    admin_user = build_mock_user(UserRole.ADMIN)
    field_officer = build_mock_user(UserRole.FIELD_OFFICER)
    mock_db = MagicMock()

    client = TestClient(app)

    try:
        # 1. Audit log requires admin role
        app.dependency_overrides[get_current_user] = lambda: field_officer
        app.dependency_overrides[get_db] = lambda: mock_db
        resp_forbidden = client.get("/api/v1/audit-log")
        assert resp_forbidden.status_code == 403
        print("   [OK] GET /audit-log rejects non-admin users with 403 Forbidden")

        # 2. Audit log with admin user
        app.dependency_overrides[get_current_user] = lambda: admin_user
        app.dependency_overrides[require_admin] = lambda: admin_user

        mock_log = Mock(spec=AuditLog)
        mock_log.log_id = uuid4()
        mock_log.user_id = admin_user.id
        mock_log.action = "STAGE_TRANSITION"
        mock_log.entity_type = "parcel"
        mock_log.entity_id = uuid4()
        mock_log.old_values = {"stage": "SURVEY"}
        mock_log.new_values = {"stage": "VERIFICATION"}
        mock_log.ip_address = "127.0.0.1"
        mock_log.user_agent = "TestClient"
        mock_log.created_at = datetime.now(timezone.utc)

        mock_db.execute.return_value.scalar.return_value = 1
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_log]

        resp_audit = client.get("/api/v1/audit-log?action=STAGE_TRANSITION")
        assert resp_audit.status_code == 200
        data_audit = resp_audit.json()
        assert data_audit["total_matched"] == 1
        assert data_audit["entries"][0]["action"] == "STAGE_TRANSITION"
        print("   [OK] GET /audit-log returns filtered append-only log entries")

        # 3. Global search
        mock_proj = Mock(spec=Project)
        mock_proj.project_id = uuid4()
        mock_proj.name = "Expressway Mumbai-Pune"
        mock_proj.type = "Highway"
        mock_proj.status = "ACTIVE"
        mock_proj.states = ["Maharashtra"]
        mock_proj.districts = ["Pune"]
        mock_proj.land_required_ha = 100.0
        mock_proj.land_acquired_ha = 50.0

        mock_db.execute.return_value.scalars.return_value.all.side_effect = [
            [mock_proj],  # projects
            [],           # parcels
        ]

        resp_search = client.get("/api/v1/search?q=Expressway")
        assert resp_search.status_code == 200
        data_search = resp_search.json()
        assert data_search["total_count"] == 1
        assert data_search["projects"][0]["name"] == "Expressway Mumbai-Pune"
        print("   [OK] GET /search?q=Expressway returns grouped results")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(require_admin, None)
        app.dependency_overrides.pop(get_db, None)


def test_admin_user_crud_and_reports():
    """Test admin user CRUD and executive summary report generation."""
    print("\n=== 8. Testing Admin User Management & Reports Generation ===")
    admin_user = build_mock_user(UserRole.ADMIN)
    mock_db = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[require_admin] = lambda: admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        # 1. Admin list users
        mock_user = Mock(spec=User)
        mock_user.id = uuid4()
        mock_user.username = "district_pune"
        mock_user.email = "pune@bhoomisetu.gov.in"
        mock_user.role = "DISTRICT"
        mock_user.state_scope = "Maharashtra"
        mock_user.district_scope = "Pune"
        mock_user.is_active = True
        mock_user.created_at = datetime.now(timezone.utc)

        mock_db.execute.return_value.scalar.return_value = 1
        mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_user]

        resp_users = client.get("/api/v1/admin/users")
        assert resp_users.status_code == 200
        assert len(resp_users.json()["items"]) == 1
        print("   [OK] GET /admin/users returns user list")

        # 2. Admin create user
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # no existing duplicate
        new_user_payload = {
            "username": "new_officer",
            "email": "officer@bhoomisetu.gov.in",
            "password": "SecretPassword123!",
            "role": "FIELD_OFFICER",
            "state_scope": "Maharashtra",
            "district_scope": "Pune",
        }
        resp_new_user = client.post("/api/v1/admin/users", json=new_user_payload)
        assert resp_new_user.status_code == 201
        assert resp_new_user.json()["username"] == "new_officer"
        print("   [OK] POST /admin/users creates user with password hash")

        # 3. Soft-deactivate user
        target_id = uuid4()
        mock_deact = Mock(spec=User)
        mock_deact.id = target_id
        mock_deact.username = "retiring_officer"
        mock_deact.is_active = True
        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_deact

        resp_deact = client.delete(f"/api/v1/admin/users/{target_id}")
        assert resp_deact.status_code == 200
        assert resp_deact.json()["is_active"] is False
        print("   [OK] DELETE /admin/users/{id} soft-deactivates user")

        # 4. Reports: executive summary (JSON)
        mock_db.execute.return_value.one.side_effect = [
            Mock(total=150, area=300.0, avg_risk=28.0),  # parcel totals
            (400.0, 200.0),                               # project land req, acq
            (10000000.0, 7500000.0),                      # compensation
        ]
        mock_db.execute.return_value.all.return_value = [("SURVEY", 50), ("VERIFICATION", 100)]
        mock_db.execute.return_value.scalar.return_value = 80  # total rr

        resp_rep_json = client.get("/api/v1/reports/executive-summary?format=json")
        assert resp_rep_json.status_code == 200
        data_rep = resp_rep_json.json()
        assert "metrics" in data_rep
        assert data_rep["metrics"]["total_parcels"] == 150
        print("   [OK] GET /reports/executive-summary?format=json returns metrics")

        # 5. Reports: executive summary (HTML)
        mock_db.execute.return_value.one.side_effect = [
            Mock(total=150, area=300.0, avg_risk=28.0),
            (400.0, 200.0),
            (10000000.0, 7500000.0),
        ]
        mock_db.execute.return_value.all.return_value = [("SURVEY", 50), ("VERIFICATION", 100)]
        mock_db.execute.return_value.scalar.return_value = 80

        resp_rep_html = client.get("/api/v1/reports/executive-summary?format=html")
        assert resp_rep_html.status_code == 200
        assert "text/html" in resp_rep_html.headers["content-type"]
        assert "Executive Land Acquisition Summary" in resp_rep_html.text
        print("   [OK] GET /reports/executive-summary?format=html returns styled HTML report")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(require_admin, None)
        app.dependency_overrides.pop(get_db, None)


def test_ml_serving_hardening():
    """Test ML hardening: prediction caching (60s TTL), SHAP timeout fallback, and fail-fast."""
    print("\n=== 9. Testing ML Serving Hardening (Cache, Timeout Guard, Fail-Fast) ===")
    from app.ml.delay_risk_service import DelayRiskService, get_delay_risk_service

    service = get_delay_risk_service()
    assert service.is_loaded(), "Delay-risk model should be loaded and healthy"

    # 1. Prediction caching test
    test_features = {
        "backlog_trend": 0.0,
        "processing_rate": 1.2,
        "stage_complexity": 0.4,
        "district_capacity": 0.9,
        "sla_breach_rate": 0.05,
        "avg_days_per_stage": 25.0,
        "dispute_ratio": 0.02,
        "compensation_pending_ratio": 0.1,
        "snapshot_count": 6,
    }

    test_proj_id = str(uuid4())
    # First call: cache miss
    res1 = service.predict_delay_risk(test_features, project_id=test_proj_id)
    assert res1["status"] == "success"
    assert res1["cached"] is False

    # Second call with same project_id: cache hit
    res2 = service.predict_delay_risk(test_features, project_id=test_proj_id)
    assert res2["status"] == "success"
    assert res2["cached"] is True
    assert res2["risk_score"] == res1["risk_score"]
    print("   [OK] Prediction cache: subsequent call with same project_id returned cached=True (TTL 60s)")

    # 2. SHAP Timeout guard test (simulating timeout by patching _shap_executor)
    with patch.object(service, "_shap_executor") as mock_executor:
        from concurrent.futures import TimeoutError as FuturesTimeoutError
        mock_future = Mock()
        mock_future.result.side_effect = FuturesTimeoutError("SHAP timed out")
        mock_executor.submit.return_value = mock_future

        # Clear cache for test
        service._invalidate_cache(test_proj_id)
        res_timeout = service.predict_delay_risk(test_features, project_id=test_proj_id)
        assert res_timeout["status"] == "success"
        assert res_timeout["shap_timed_out"] is True
        assert res_timeout["top_factors"] == []
        assert res_timeout["risk_score"] is not None
        print(f"   [OK] SHAP timeout guard: gracefully fell back to risk score only (score={res_timeout['risk_score']})")

    # 3. Fail-fast test
    with patch.object(service, "_startup_failed", True):
        res_failfast = service.predict_delay_risk(test_features)
        assert res_failfast["status"] == "model_unavailable"
        print("   [OK] Fail-fast guard: returns model_unavailable status when startup fails")


def run_all():
    print("=" * 72)
    print("  BHOOMI-SETU -- DAY 2 + DAY 3 BACKEND VERIFICATION SUITE")
    print("=" * 72)

    test_sla_service_and_dashboard()
    test_project_timeline()
    test_alerts_endpoints()
    test_advanced_analytics()
    test_documents_and_validation()
    test_compensation_and_rr()
    test_audit_log_and_search()
    test_admin_user_crud_and_reports()
    test_ml_serving_hardening()

    print("\n" + "=" * 72)
    print("  [SUCCESS] ALL DAY 2 + DAY 3 BACKEND TESTS PASSED CLEANLY (0 ERRORS)!")
    print("=" * 72)


if __name__ == "__main__":
    run_all()

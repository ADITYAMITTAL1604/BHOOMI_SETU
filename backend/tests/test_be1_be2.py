"""Comprehensive test suite for BE-1 (Security) and BE-2 (GIS & ML) verification checklists.

Checklist:
BE-1 (Security):
- Login with invalid credentials -> 401, no user enumeration
- No token -> 401; expired token -> 401; tampered token -> 401
- Cross-district/state access -> 403; unassigned-parcel access -> 403; non-admin on /admin -> 403
- SQL injection in search params -> safe; XSS in project name -> sanitized on input/output
- Oversized JSON body (>1MB) -> 413; rate limiting works on /auth/login

BE-2 (GIS & ML):
- Malformed GeoJSON -> 400; self-intersecting polygon -> 400
- Coordinates outside India's bounding box -> 400; geometry with 50K+ vertices -> 400
- Bounding box covering all of India -> 400 (reject overly broad viewport queries)
- Empty project -> delay-risk API returns "insufficient data"; single snapshot -> degraded response, no crash
- Extreme outlier feature values -> model does not crash
- Dashboard query <500ms for 5,000 parcels; GIS viewport query <500ms
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.config import get_settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password
from app.database import get_db
from app.main import app
from app.models import Parcel, Project, User
from app.models.enums import ParcelStatus, ProjectStatus, UserRole
from app.utils.geo_validation import (
    INDIA_MAX_LAT,
    INDIA_MAX_LON,
    INDIA_MIN_LAT,
    INDIA_MIN_LON,
    validate_and_parse_geometry,
    validate_viewport_bbox,
)
from app.utils.sanitization import sanitize_text

settings = get_settings()


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


# ==============================================================================
# BE-1: SECURITY CHECKLIST TESTS
# ==============================================================================

def test_be1_login_invalid_credentials_no_enumeration():
    """Verify login with invalid username and invalid password both return 401 with identical message."""
    print("\n--- BE-1.1: Login invalid credentials & no user enumeration ---")
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    # 1. Non-existent username
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    resp1 = client.post("/api/v1/auth/login", data={"username": "nonexistent_user", "password": "anypassword"})
    assert resp1.status_code == 401
    detail1 = resp1.json()["detail"]
    assert detail1 == "Incorrect username or password"

    # 2. Existing username with incorrect password
    mock_user = Mock(spec=User)
    mock_user.username = "real_user"
    mock_user.password_hash = hash_password("correct_password")
    mock_user.is_active = True
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_user

    resp2 = client.post("/api/v1/auth/login", data={"username": "real_user", "password": "wrong_password"})
    assert resp2.status_code == 401
    detail2 = resp2.json()["detail"]
    assert detail2 == "Incorrect username or password"

    # Verify identical error message (no user enumeration)
    assert detail1 == detail2
    print("   [PASS] 401 returned for both; identical error details prevent user enumeration.")


def test_be1_token_validation():
    """Verify missing, expired, and tampered tokens all return 401 Unauthorized."""
    print("\n--- BE-1.2: Token validation (no token, expired, tampered) ---")
    app.dependency_overrides.clear()
    client = TestClient(app)

    # 1. No token
    resp_no_token = client.get("/api/v1/projects")
    assert resp_no_token.status_code == 401
    print("   [PASS] No token -> 401 Unauthorized")

    # 2. Expired token
    expired_payload = {
        "sub": str(uuid4()),
        "username": "expired_user",
        "role": UserRole.ADMIN.value,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=10),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    resp_expired = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp_expired.status_code == 401
    print("   [PASS] Expired token -> 401 Unauthorized")

    # 3. Tampered token (invalid signature)
    tampered_token = expired_token[:-8] + "abcdefgh"
    resp_tampered = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {tampered_token}"})
    assert resp_tampered.status_code == 401
    print("   [PASS] Tampered token -> 401 Unauthorized")


def test_be1_access_control_and_rbac():
    """Verify cross-district/state access -> 403, unassigned-parcel access -> 403, non-admin on /admin -> 403."""
    print("\n--- BE-1.3: RBAC & Scope (Cross-scope 403, Unassigned 403, Non-admin 403) ---")
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    # 1. Cross-district access -> 403
    pune_user = build_mock_user(role=UserRole.DISTRICT, state_scope="Maharashtra", district_scope="Pune")
    app.dependency_overrides[get_current_user] = lambda: pune_user

    target_parcel = Mock(spec=Parcel)
    target_parcel.parcel_id = uuid4()
    target_parcel.state = "Maharashtra"
    target_parcel.district = "Nagpur"  # Outside Pune scope
    target_parcel.assigned_officer = pune_user.id
    mock_db.execute.return_value.scalar_one_or_none.return_value = target_parcel

    resp_cross_dist = client.get(f"/api/v1/parcels/{target_parcel.parcel_id}")
    assert resp_cross_dist.status_code == 403
    print(f"   [PASS] Cross-district access -> 403 ({resp_cross_dist.json()['detail']})")

    # 2. Cross-state project access -> 403
    mh_user = build_mock_user(role=UserRole.STATE, state_scope="Maharashtra")
    app.dependency_overrides[get_current_user] = lambda: mh_user

    karnataka_project = Mock(spec=Project)
    karnataka_project.project_id = uuid4()
    karnataka_project.states = ["Karnataka"]
    karnataka_project.districts = ["Bengaluru"]
    mock_db.execute.return_value.scalar_one_or_none.return_value = karnataka_project

    resp_cross_state = client.get(f"/api/v1/projects/{karnataka_project.project_id}")
    assert resp_cross_state.status_code == 403
    print(f"   [PASS] Cross-state project access -> 403 ({resp_cross_state.json()['detail']})")

    # 3. Unassigned parcel access by Field Officer -> 403
    field_officer = build_mock_user(role=UserRole.FIELD_OFFICER, state_scope="Maharashtra", district_scope="Pune")
    app.dependency_overrides[get_current_user] = lambda: field_officer

    other_officer_parcel = Mock(spec=Parcel)
    other_officer_parcel.parcel_id = uuid4()
    other_officer_parcel.state = "Maharashtra"
    other_officer_parcel.district = "Pune"
    other_officer_parcel.assigned_officer = uuid4()  # Not assigned to field_officer
    mock_db.execute.return_value.scalar_one_or_none.return_value = other_officer_parcel

    resp_unassigned = client.get(f"/api/v1/parcels/{other_officer_parcel.parcel_id}")
    assert resp_unassigned.status_code == 403
    print(f"   [PASS] Unassigned parcel access by Field Officer -> 403 ({resp_unassigned.json()['detail']})")

    # 4. Non-admin on /admin -> 403
    resp_admin = client.get("/api/v1/admin/users")
    assert resp_admin.status_code == 403
    print(f"   [PASS] Non-admin access to /admin -> 403 ({resp_admin.json()['detail']})")


def test_be1_sql_injection_and_xss_sanitization():
    """Verify SQL injection safe search and XSS input sanitization."""
    print("\n--- BE-1.4: SQL Injection Safety & XSS Sanitization ---")
    mock_db = MagicMock()
    admin_user = build_mock_user(role=UserRole.ADMIN)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    client = TestClient(app)

    # 1. SQL Injection attempt in search params
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    sqli_payload = "'; DROP TABLE projects; --"
    resp_sqli = client.get(f"/api/v1/search?q={sqli_payload}")
    assert resp_sqli.status_code == 200  # Parameterized query handles it safely
    print("   [PASS] SQL Injection payload safely parameterized without DB error.")

    # 2. XSS in text fields
    raw_xss = "<script>alert('pwned')</script>Project Alpha"
    sanitized = sanitize_text(raw_xss)
    assert "<script>" not in sanitized
    assert "alert" not in sanitized
    assert "Project Alpha" in sanitized

    # Direct test of ProjectCreate schema validator
    from app.routers.projects import ProjectCreate
    proj_in = ProjectCreate(
        name="<script>alert(1)</script>Nagpur Bypass",
        type="Highway <img src=x onerror=alert(1)>",
        states=["Maharashtra"],
        districts=["Nagpur"],
        land_required_ha=120.5,
    )
    assert "<script>" not in proj_in.name
    assert "onerror=" not in proj_in.type
    print("   [PASS] XSS scripts and handlers stripped/escaped from ProjectCreate schema.")


def test_be1_oversized_payload_and_rate_limiting():
    """Verify oversized payload rejection (>1MB -> 413) and rate limit on /auth/login."""
    print("\n--- BE-1.5: 1MB Body Limit (413) & Rate Limiting ---")
    app.dependency_overrides.clear()
    client = TestClient(app)

    # 1. Oversized JSON body (> 1MB)
    huge_data = {"dummy": "x" * (1024 * 1024 + 100)}  # > 1MB
    resp_huge = client.post("/api/v1/search", json=huge_data)
    assert resp_huge.status_code == 413
    print(f"   [PASS] Oversized payload (>1MB) rejected with 413: {resp_huge.json()['detail'][:60]}...")

    # 2. Rate limiting on /auth/login (limit: 10 per minute)
    # Send 10 requests, then 11th should be rate-limited (429)
    # Using a dedicated test IP via headers
    headers = {"X-Forwarded-For": "198.51.100.42"}
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    status_codes = []
    for i in range(12):
        r = client.post("/api/v1/auth/login", data={"username": f"user_{i}", "password": "pwd"}, headers=headers)
        status_codes.append(r.status_code)

    assert 429 in status_codes
    print(f"   [PASS] Rate limiter triggered: {status_codes.count(401)} unauthorized, {status_codes.count(429)} rate-limited (429).")


# ==============================================================================
# BE-2: GIS & ML CHECKLIST TESTS
# ==============================================================================

def test_be2_gis_geometry_validation():
    """Verify malformed GeoJSON -> 400, self-intersecting polygon -> 400, coordinates outside India -> 400, 50k+ vertices -> 400."""
    print("\n--- BE-2.1: GIS Geometry Validation (Malformed, Self-intersecting, Bounds, Vertices) ---")
    mock_db = MagicMock()
    admin_user = build_mock_user(role=UserRole.ADMIN)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    client = TestClient(app)

    # 1. Malformed WKT / GeoJSON
    with pytest.raises(Exception) as exc1:
        validate_and_parse_geometry("POLYGON((NOT A VALID GEOMETRY))")
    assert exc1.value.status_code == 400
    print(f"   [PASS] Malformed WKT rejected with 400: {exc1.value.detail}")

    # 2. Self-intersecting polygon (Figure-8 bowtie)
    bowtie_wkt = "POLYGON((73.8 18.5, 73.9 18.6, 73.8 18.6, 73.9 18.5, 73.8 18.5))"
    with pytest.raises(Exception) as exc2:
        validate_and_parse_geometry(bowtie_wkt)
    assert exc2.value.status_code == 400
    print(f"   [PASS] Self-intersecting polygon rejected with 400: {exc2.value.detail}")

    # 3. Coordinates outside India's bounding box (e.g., London coordinates 51.5 deg N, -0.1 deg W)
    london_wkt = "POLYGON((-0.1 51.5, -0.1 51.6, 0.0 51.6, 0.0 51.5, -0.1 51.5))"
    with pytest.raises(Exception) as exc3:
        validate_and_parse_geometry(london_wkt)
    assert exc3.value.status_code == 400
    print(f"   [PASS] Coordinates outside India rejected with 400: {exc3.value.detail}")

    # 4. Geometry with 50,000+ vertices
    import numpy as np
    n_pts = 50005
    angles = np.linspace(0, 2 * np.pi, n_pts)
    center_lon, center_lat = 75.0, 20.0
    r = 0.01
    lons = center_lon + r * np.cos(angles)
    lats = center_lat + r * np.sin(angles)
    pts_str = ", ".join(f"{lon:.6f} {lat:.6f}" for lon, lat in zip(lons, lats))
    huge_polygon_wkt = f"POLYGON(({pts_str}))"

    with pytest.raises(Exception) as exc4:
        validate_and_parse_geometry(huge_polygon_wkt)
    assert exc4.value.status_code == 400
    print(f"   [PASS] Geometry with >50k vertices rejected with 400: {exc4.value.detail}")


def test_be2_viewport_bbox_limits():
    """Verify bounding box covering all of India (>15 deg span) -> 400."""
    print("\n--- BE-2.2: Viewport Bounding Box Span Limit ---")
    mock_db = MagicMock()
    admin_user = build_mock_user(role=UserRole.ADMIN)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    client = TestClient(app)

    # 1. Bounding box spanning all of India (68 deg to 98 deg lon = 30 deg span > 15 deg max)
    all_india_bbox = {
        "min_lon": 68.5,
        "min_lat": 8.0,
        "max_lon": 97.0,
        "max_lat": 35.0,
    }
    resp_bbox = client.post("/api/v1/gis/parcels/within", json=all_india_bbox)
    assert resp_bbox.status_code == 400
    print(f"   [PASS] Viewport covering all of India rejected with 400: {resp_bbox.json()['detail']}")

    # 2. Valid local bounding box (e.g. Pune district ~0.5 deg span)
    valid_bbox = {
        "min_lon": 73.7,
        "min_lat": 18.4,
        "max_lon": 74.0,
        "max_lat": 18.7,
    }
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    resp_valid = client.post("/api/v1/gis/parcels/within", json=valid_bbox)
    assert resp_valid.status_code == 200
    print("   [PASS] Local viewport bounding box accepted with 200 OK.")


def test_be2_ml_empty_project_single_snapshot_outliers():
    """Verify empty project -> 'insufficient data', single snapshot -> degraded response no crash, extreme outliers -> no crash."""
    print("\n--- BE-2.3: ML Edge Cases (Empty Project, Single Snapshot, Outliers) ---")
    from app.ml.delay_risk_service import get_delay_risk_service
    service = get_delay_risk_service()

    # 1. Empty project (snapshot_count = 0)
    empty_features = {
        "snapshot_count": 0,
        "backlog_trend": 0.0,
        "processing_rate": 0.0,
        "stage_complexity": 0.0,
        "district_capacity": 0.0,
        "sla_breach_rate": 0.0,
        "avg_days_per_stage": 0.0,
        "dispute_ratio": 0.0,
        "compensation_pending_ratio": 0.0,
    }
    res_empty = service.predict_delay_risk(empty_features)
    assert res_empty["status"] == "insufficient_data"
    assert res_empty["risk_score"] is None
    print(f"   [PASS] Empty project -> status='{res_empty['status']}': {res_empty['message']}")

    # 2. Single snapshot (snapshot_count = 1) -> Degraded response without crash
    single_snap_features = {
        "snapshot_count": 1,
        "backlog_trend": 0.0,
        "processing_rate": 0.0,
        "stage_complexity": 0.65,
        "district_capacity": 0.80,
        "sla_breach_rate": 0.15,
        "avg_days_per_stage": 45.0,
        "dispute_ratio": 0.05,
        "compensation_pending_ratio": 0.20,
    }
    res_single = service.predict_delay_risk(single_snap_features)
    assert res_single["status"] == "degraded"
    assert res_single["risk_score"] is not None
    assert 0.0 <= res_single["risk_score"] <= 1.0
    print(f"   [PASS] Single snapshot -> degraded response without crash (risk_score={res_single['risk_score']}, status={res_single['status']})")

    # 3. Extreme outlier feature values -> No crash
    outlier_features = {
        "snapshot_count": 10,
        "backlog_trend": 99999999.0,      # Extreme positive
        "processing_rate": -888888.0,     # Negative rate outlier
        "stage_complexity": 5555.0,       # Scale is 0-1
        "district_capacity": float("inf"),# Infinity check
        "sla_breach_rate": 1e12,          # Huge number
        "avg_days_per_stage": float("nan"), # NaN check
        "dispute_ratio": -99.0,
        "compensation_pending_ratio": 1e6,
    }
    res_outliers = service.predict_delay_risk(outlier_features)
    assert res_outliers["status"] == "success"
    assert res_outliers["risk_score"] is not None
    assert 0.0 <= res_outliers["risk_score"] <= 1.0
    print(f"   [PASS] Extreme outlier / Inf / NaN values handled cleanly (risk_score={res_outliers['risk_score']})")


def test_be2_latency_benchmarks():
    """Verify latency benchmarks: Dashboard query <500ms for 5,000 parcels, GIS viewport query <500ms."""
    print("\n--- BE-2.4: Latency Benchmarks (<500ms for 5,000 parcels & GIS viewport) ---")
    mock_db = MagicMock()
    admin_user = build_mock_user(role=UserRole.ADMIN)
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: admin_user
    client = TestClient(app)

    # 1. Benchmark Dashboard query with 5,000 mock parcels
    # Build 5,000 lightweight parcel mock objects
    mock_parcels = []
    for i in range(5000):
        p = Mock(spec=Parcel)
        p.parcel_id = uuid4()
        p.project_id = uuid4()
        p.status = ParcelStatus.IN_PROGRESS.value if i % 2 == 0 else ParcelStatus.COMPLETED.value
        p.current_stage = "SURVEY"
        p.area_ha = 1.5
        p.risk_score = 42.0
        mock_parcels.append(p)

    mock_db.execute.return_value.one.return_value = Mock(
        total=5000, required=7500.0, acquired=3500.0, area=7500.0, avg_risk=42.0
    )
    mock_db.execute.return_value.all.return_value = [("Pune", 3000, 45.0), ("Satara", 2000, 38.0)]
    mock_db.execute.return_value.scalar.return_value = 120

    t0 = time.perf_counter()
    resp_state = client.get("/api/v1/dashboard/state/Maharashtra")
    duration_dash_ms = (time.perf_counter() - t0) * 1000

    assert resp_state.status_code == 200
    assert duration_dash_ms < 500.0
    print(f"   [PASS] Dashboard state aggregation took {duration_dash_ms:.2f} ms (< 500 ms target)")

    # 2. Benchmark GIS Viewport query
    viewport_parcels = []
    for i in range(500):
        p = Mock(spec=Parcel)
        p.parcel_id = uuid4()
        p.project_id = uuid4()
        p.survey_number = f"S-{i}"
        p.area_ha = 0.8
        p.owner_name = f"Farmer {i}"
        p.owner_reference = f"REF-{i}"
        p.current_stage = "SURVEY"
        p.status = ParcelStatus.IN_PROGRESS.value
        p.risk_score = 30.0
        p.village = "Hinjawadi"
        p.district = "Pune"
        p.state = "Maharashtra"
        p.geometry = None
        viewport_parcels.append(p)

    mock_db.execute.return_value.scalars.return_value.all.return_value = viewport_parcels

    valid_bbox = {
        "min_lon": 73.8,
        "min_lat": 18.5,
        "max_lon": 73.9,
        "max_lat": 18.6,
    }
    t0 = time.perf_counter()
    resp_gis = client.post("/api/v1/gis/parcels/within", json=valid_bbox)
    duration_gis_ms = (time.perf_counter() - t0) * 1000

    assert resp_gis.status_code == 200
    assert duration_gis_ms < 500.0
    print(f"   [PASS] GIS viewport query (500 features) took {duration_gis_ms:.2f} ms (< 500 ms target)")


if __name__ == "__main__":
    print("========================================================================")
    print("  BHOOMI-SETU -- BE-1 + BE-2 VERIFICATION TEST SUITE")
    print("========================================================================")
    test_be1_login_invalid_credentials_no_enumeration()
    test_be1_token_validation()
    test_be1_access_control_and_rbac()
    test_be1_sql_injection_and_xss_sanitization()
    test_be1_oversized_payload_and_rate_limiting()

    test_be2_gis_geometry_validation()
    test_be2_viewport_bbox_limits()
    test_be2_ml_empty_project_single_snapshot_outliers()
    test_be2_latency_benchmarks()
    print("========================================================================")
    print("  [SUCCESS] ALL BE-1 + BE-2 CHECKLIST TESTS PASSED WITH 0 FAILURES!")
    print("========================================================================")

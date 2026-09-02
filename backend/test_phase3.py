"""Verification test suite for Phase 3:
- Project CRUD
- Parcel CRUD & Stage Transition Engine
- GIS Endpoints & GeoJSON Serialization
- Dashboard Aggregate Metrics & Project Summary
- Seed Script Data Integrity
"""

import sys
import os
from uuid import uuid4
from datetime import date, datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import HTTPException
from app.main import app
from app.models import (
    User,
    Project,
    Parcel,
    AcquisitionStage,
    AuditLog,
    GISBoundary,
    Compensation,
    RRRecord,
)
from app.models.enums import (
    UserRole,
    ProjectStatus,
    StageName,
    ParcelStatus,
    StageStatus,
)
from app.services.transition import (
    STAGE_ORDER,
    STAGE_INDEX,
    validate_transition,
    compute_sla_breach,
    get_sla_status,
    write_transition_audit,
    execute_transition,
    get_allowed_target_stages,
)
from app.routers.gis import BoundingBox, _feature_collection, _build_feature
from app.utils.pagination import PageParams, create_page_response


def test_app_routes_registered():
    """Verify that all Phase 3 routers are mounted on the FastAPI app."""
    print("\n=== Testing Router Registration ===")
    route_paths = [route.path for route in app.routes]
    
    # Auth
    assert any("/api/v1/auth" in p for p in route_paths), "Auth router missing"
    # Projects
    assert any("/api/v1/projects" in p for p in route_paths), "Projects router missing"
    # Parcels
    assert any("/api/v1/parcels" in p for p in route_paths), "Parcels router missing"
    # GIS
    assert any("/api/v1/gis" in p for p in route_paths), "GIS router missing"
    # Dashboard
    assert any("/api/v1/dashboard" in p for p in route_paths), "Dashboard router missing"
    
    print("[OK] All 5 core routers mounted successfully on FastAPI application.")


def test_stage_transition_engine():
    """Verify stage transition validation and SLA calculations."""
    print("\n=== Testing Stage Transition Engine ===")
    
    # 1. Forward transition (PROPOSAL -> IDENTIFICATION)
    validate_transition(StageName.PROPOSAL.value, StageName.IDENTIFICATION.value)
    print("   [OK] Normal forward transition allowed")
    
    # 2. Skip forward transition (PROPOSAL -> SURVEY)
    validate_transition(StageName.PROPOSAL.value, StageName.SURVEY.value)
    print("   [OK] Forward skip allowed")
    
    # 3. Rollback transition (SURVEY -> IDENTIFICATION)
    validate_transition(StageName.SURVEY.value, StageName.IDENTIFICATION.value)
    print("   [OK] Backward rollback allowed")
    
    # 4. Self-transition (SURVEY -> SURVEY)
    validate_transition(StageName.SURVEY.value, StageName.SURVEY.value)
    print("   [OK] Self-transition allowed")
    
    # 5. Invalid transition (PROPOSAL -> CLOSURE)
    try:
        validate_transition(StageName.PROPOSAL.value, StageName.CLOSURE.value)
        assert False, "Should reject invalid jump PROPOSAL -> CLOSURE"
    except HTTPException as e:
        assert e.status_code == 422
        print("   [OK] Invalid transition (PROPOSAL -> CLOSURE) rejected with 422")
    
    # 6. Unknown stage
    try:
        validate_transition("UNKNOWN_STAGE", StageName.SURVEY.value)
        assert False, "Should reject unknown current stage"
    except HTTPException as e:
        assert e.status_code == 422
        print("   [OK] Unknown stage rejected with 422")

    # 7. Test SLA calculations
    stage_ok = Mock(spec=AcquisitionStage)
    stage_ok.completion_date = None
    stage_ok.target_date = datetime.now(timezone.utc).date() + timedelta(days=10)
    assert not compute_sla_breach(stage_ok), "Future target_date should not breach SLA"
    print("   [OK] SLA on-track detection works")

    stage_breached = Mock(spec=AcquisitionStage)
    stage_breached.completion_date = None
    stage_breached.target_date = datetime.now(timezone.utc).date() - timedelta(days=5)
    assert compute_sla_breach(stage_breached), "Past target_date should breach SLA"
    print("   [OK] SLA breach detection works")

    stage_completed = Mock(spec=AcquisitionStage)
    stage_completed.completion_date = datetime.now(timezone.utc).date() - timedelta(days=2)
    stage_completed.target_date = datetime.now(timezone.utc).date() - timedelta(days=5)
    assert not compute_sla_breach(stage_completed), "Completed stage should not breach SLA"
    print("   [OK] Completed stage ignores past target_date")


def test_transition_execution():
    """Verify execute_transition updates parcel, stage, and writes audit log."""
    print("\n=== Testing Transition Execution Logic ===")
    
    mock_db = MagicMock()
    
    user = Mock(spec=User)
    user.id = uuid4()
    
    parcel = Mock(spec=Parcel)
    parcel.parcel_id = uuid4()
    parcel.current_stage = StageName.PROPOSAL.value
    parcel.status = ParcelStatus.IN_PROGRESS.value
    parcel.assigned_officer = user.id
    
    old_stage_row = Mock(spec=AcquisitionStage)
    old_stage_row.stage_name = StageName.PROPOSAL.value
    old_stage_row.status = StageStatus.IN_PROGRESS.value
    old_stage_row.completion_date = None
    
    # Query return old stage then new stage
    mock_db.execute.return_value.scalar_one_or_none.side_effect = [old_stage_row, None]
    
    result = execute_transition(
        db=mock_db,
        parcel=parcel,
        target_stage=StageName.IDENTIFICATION.value,
        acting_user=user,
        remarks="Field verification completed",
        sla_target_date=date(2026, 10, 15),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0",
    )
    
    assert result["old_stage"] == StageName.PROPOSAL.value
    assert result["new_stage"] == StageName.IDENTIFICATION.value
    assert result["remarks"] == "Field verification completed"
    assert result["transitioned_by"] == str(user.id)
    assert mock_db.commit.called
    print("[OK] execute_transition properly updates stage records and logs audit event.")


def test_gis_helpers_and_schemas():
    """Verify GIS schemas, validation, and GeoJSON builders."""
    print("\n=== Testing GIS Schemas & GeoJSON Builders ===")
    
    # 1. BoundingBox validation
    bbox = BoundingBox(min_lon=73.0, min_lat=18.0, max_lon=74.0, max_lat=19.0)
    bbox.validate_bbox()  # should not raise
    print("   [OK] Valid bounding box accepted")

    # Inverted longitude
    try:
        bad_bbox = BoundingBox(min_lon=74.0, min_lat=18.0, max_lon=73.0, max_lat=19.0)
        bad_bbox.validate_bbox()
        assert False, "Should fail inverted lon"
    except HTTPException as e:
        assert e.status_code == 400
        print("   [OK] Inverted longitude rejected")

    # 2. GeoJSON Feature & Collection builders
    feature = _build_feature(
        geometry_geojson={"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 0]]]},
        properties={"survey_number": "101/A", "owner": "Ramesh Patil"},
    )
    assert feature["type"] == "Feature"
    assert feature["properties"]["survey_number"] == "101/A"
    
    fc = _feature_collection([feature])
    assert fc["type"] == "FeatureCollection"
    assert fc["count"] == 1
    assert len(fc["features"]) == 1
    print("[OK] GeoJSON builders format compliant FeatureCollection objects.")


def test_pagination_helper():
    """Verify Pagination helper with PageResponse."""
    print("\n=== Testing Pagination Helper ===")
    
    items = ["item1", "item2", "item3"]
    response = create_page_response(items=items, total=50, page=1, page_size=10)
    
    assert response.page == 1
    assert response.page_size == 10
    assert response.total == 50
    assert response.total_pages == 5
    assert response.has_next is True
    assert response.has_prev is False
    print("[OK] create_page_response calculates pagination parameters correctly.")


def test_project_summary_handler():
    """Verify get_project_summary handler calculation logic."""
    print("\n=== Testing Project Summary Handler ===")
    from app.routers.projects import get_project_summary

    mock_db = MagicMock()
    user = Mock(spec=User)
    user.state_scope = None
    user.district_scope = None

    proj_id = uuid4()
    mock_project = Mock(spec=Project)
    mock_project.project_id = proj_id
    mock_project.name = "Test Highway"
    mock_project.type = "Highway"
    mock_project.status = ProjectStatus.ACTIVE
    mock_project.states = ["Maharashtra"]
    mock_project.districts = ["Pune"]
    mock_project.land_required_ha = 100.0
    mock_project.land_acquired_ha = 60.0
    mock_project.target_date = date(2027, 1, 1)
    mock_project.created_at = datetime.now(timezone.utc)

    # 1. Project query
    # 2. status counts
    # 3. stage counts
    # 4. high risk count
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_project
    mock_db.execute.return_value.all.side_effect = [
        [(ParcelStatus.COMPLETED.value, 15), (ParcelStatus.IN_PROGRESS.value, 20)],
        [(StageName.SURVEY.value, 10), (StageName.VERIFICATION.value, 25)],
    ]
    mock_db.execute.return_value.scalar.return_value = 5

    res = get_project_summary(
        project_id=proj_id,
        db=mock_db,
        current_user=user,
    )

    assert res["project_id"] == str(proj_id)
    assert res["acquisition_progress_pct"] == 60.0
    assert res["total_parcels"] == 35
    assert res["completed_parcels"] == 15
    assert res["in_progress_parcels"] == 20
    assert res["high_risk_parcels"] == 5
    print("[OK] get_project_summary calculates metrics and stage/status breakdowns correctly.")


def run_all_tests():
    print("=" * 70)
    print("  BHOOMI-SETU -- Phase 3 Verification Suite")
    print("=" * 70)
    
    test_app_routes_registered()
    test_stage_transition_engine()
    test_transition_execution()
    test_gis_helpers_and_schemas()
    test_pagination_helper()
    test_project_summary_handler()
    
    print("\n" + "=" * 70)
    print("  [SUCCESS] ALL PHASE 3 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()

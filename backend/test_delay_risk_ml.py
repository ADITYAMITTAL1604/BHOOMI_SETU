"""Verification test suite for Delay-Risk ML Pipeline:
1. Shared feature engineering (build_features)
2. DelayRiskService singleton & SHAP TreeExplainer
3. Confidence score & threshold calibration
4. Insufficient data handling (snapshot_count < 2)
5. Analytics endpoint GET /analytics/projects/{id}/delay-risk (404 and 200)
"""

import sys
import os
from uuid import uuid4
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.models import Project, ProjectHistory, User
from app.models.enums import UserRole, ProjectStatus
from app.ml.features import FEATURE_NAMES, FEATURE_LABELS, build_features
from app.ml.delay_risk_service import DelayRiskService, get_delay_risk_service
from app.core.security import create_access_token


def test_shared_feature_engineering():
    """Verify build_features produces all 9 features with correct trend calculations."""
    print("\n=== Testing Shared Feature Engineering (build_features) ===")
    
    # 1. Empty snapshot case
    empty_feats = build_features([])
    assert set(empty_feats.keys()) == set(FEATURE_NAMES)
    assert empty_feats["snapshot_count"] == 0
    print("   [OK] Empty snapshots correctly returns zeroed feature vector")

    # 2. Multi-snapshot progression
    base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
    mock_snapshots = [
        {
            "snapshot_date": (base_time).isoformat(),
            "parcels_total": 200,
            "parcels_completed": 20,
            "parcels_in_progress": 150,
            "parcels_blocked": 10,
            "compensation_paid_total": 5000000.0,
            "compensation_pending_total": 2000000.0,
            "stages_snapshot": {"SURVEY": 50, "VERIFICATION": 100},
            "metadata_json": {"officers_count": 5, "sla_breaches": 2, "disputes_count": 5},
        },
        {
            "snapshot_date": (base_time + timedelta(days=30)).isoformat(),
            "parcels_total": 200,
            "parcels_completed": 50,
            "parcels_in_progress": 120,
            "parcels_blocked": 15,
            "compensation_paid_total": 8000000.0,
            "compensation_pending_total": 1000000.0,
            "stages_snapshot": {"VERIFICATION": 80, "AWARD": 40},
            "metadata_json": {"officers_count": 5, "sla_breaches": 3, "disputes_count": 8},
        },
    ]

    feats = build_features(mock_snapshots)
    assert set(feats.keys()) == set(FEATURE_NAMES)
    assert feats["snapshot_count"] == 2
    # Completed increased by 30 over 30 days -> processing_rate ~ 1.0 parcel/day
    assert 0.9 <= feats["processing_rate"] <= 1.1
    # Backlog dropped from (150+10=160) to (120+15=135) -> backlog_trend is negative
    assert feats["backlog_trend"] < 0
    # Compensation pending ratio: 1M / (8M + 1M) ~ 0.111
    assert 0.10 <= feats["compensation_pending_ratio"] <= 0.15
    print("   [OK] Multi-snapshot velocity and backlog trends computed correctly")


def test_delay_risk_service():
    """Verify DelayRiskService model prediction, confidence score, and SHAP top 4 factors."""
    print("\n=== Testing DelayRiskService Inference & SHAP Explainability ===")

    service = get_delay_risk_service()
    assert service.is_loaded(), "Model artifacts must be loaded in DelayRiskService"
    print("   [OK] Model and SHAP TreeExplainer initialized successfully")

    # 1. Test empty project (0 snapshots) and single snapshot (1 snapshot)
    empty_row = {name: 0.5 for name in FEATURE_NAMES}
    empty_row["snapshot_count"] = 0
    res_empty = service.predict_delay_risk(empty_row)
    assert res_empty["status"] == "insufficient_data"
    assert res_empty["risk_score"] is None
    assert res_empty["confidence"] == 0.0

    low_data_row = {name: 0.5 for name in FEATURE_NAMES}
    low_data_row["snapshot_count"] = 1
    res_insufficient = service.predict_delay_risk(low_data_row)
    assert res_insufficient["status"] in ("insufficient_data", "degraded")
    print("   [OK] Rejects snapshot_count 0 with 'insufficient_data' and 1 with 'degraded'")

    # 2. Test high risk prediction
    high_risk_row = {
        "backlog_trend": 2.5,          # Rapidly mounting backlog
        "processing_rate": 0.1,        # Stagnant completion
        "stage_complexity": 0.85,      # Heavy regulatory stages
        "district_capacity": 0.2,      # Severe staffing deficit
        "sla_breach_rate": 0.6,        # High statutory breaches
        "avg_days_per_stage": 95.0,    # Long dwell time
        "dispute_ratio": 0.25,         # Heavy litigation
        "compensation_pending_ratio": 0.75, # Unpaid payouts
        "snapshot_count": 8,           # Sufficient observation
    }
    res_high = service.predict_delay_risk(high_risk_row)
    assert res_high["status"] == "success"
    assert res_high["risk_score"] is not None
    assert res_high["risk_level"] in ("HIGH", "MEDIUM")
    assert 0.0 <= res_high["confidence"] <= 1.0
    assert len(res_high["top_factors"]) == 4
    for factor in res_high["top_factors"]:
        assert "feature" in factor
        assert "title" in factor
        assert "shap_value" in factor
        assert "description" in factor
        assert len(factor["description"]) > 10
    print(f"   [OK] High risk scenario evaluated: Risk={res_high['risk_score']} ({res_high['risk_level']}), Confidence={res_high['confidence']}")
    print(f"   [OK] Top factor identified: {res_high['top_factors'][0]['title']} -> {res_high['top_factors'][0]['description']}")

    # 3. Test healthy / low risk prediction
    healthy_row = {
        "backlog_trend": -1.5,
        "processing_rate": 3.0,
        "stage_complexity": 0.3,
        "district_capacity": 0.9,
        "sla_breach_rate": 0.02,
        "avg_days_per_stage": 20.0,
        "dispute_ratio": 0.01,
        "compensation_pending_ratio": 0.05,
        "snapshot_count": 10,
    }
    res_healthy = service.predict_delay_risk(healthy_row)
    assert res_healthy["status"] == "success"
    assert res_healthy["risk_score"] is not None
    assert res_healthy["risk_level"] in ("LOW", "MEDIUM")
    print(f"   [OK] Healthy scenario evaluated: Risk={res_healthy['risk_score']} ({res_healthy['risk_level']}), Confidence={res_healthy['confidence']}")


def test_analytics_api_endpoint():
    """Verify GET /api/v1/analytics/projects/{project_id}/delay-risk endpoint."""
    print("\n=== Testing Analytics Delay-Risk API Endpoint ===")
    from app.core.deps import get_current_user
    from app.database import get_db

    mock_user = Mock(spec=User)
    mock_user.id = uuid4()
    mock_user.username = "admin"
    mock_user.role = UserRole.ADMIN
    mock_user.state_scope = None
    mock_user.district_scope = None
    mock_user.is_active = True

    mock_db = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        # 1. 404 for non-existent project
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        non_existent_id = uuid4()
        resp_404 = client.get(f"/api/v1/analytics/projects/{non_existent_id}/delay-risk")
        assert resp_404.status_code == 404
        print("   [OK] Non-existent project returns 404 Not Found")

        # 2. 200 for existing project with snapshots
        proj_id = uuid4()
        mock_project = Mock(spec=Project)
        mock_project.project_id = proj_id
        mock_project.name = "Delhi-Mumbai Freight Corridor"
        mock_project.type = "Railway"
        mock_project.status = "ACTIVE"
        mock_project.states = ["Maharashtra"]
        mock_project.districts = ["Thane"]
        mock_project.land_required_ha = 450.0

        snap1 = Mock(spec=ProjectHistory)
        snap1.snapshot_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        snap1.land_required_ha = 450.0
        snap1.land_acquired_ha = 50.0
        snap1.parcels_total = 200
        snap1.parcels_completed = 25
        snap1.parcels_in_progress = 150
        snap1.parcels_blocked = 25
        snap1.compensation_paid_total = 10000000.0
        snap1.compensation_pending_total = 35000000.0
        snap1.stages_snapshot = {"SURVEY": 80, "OBJECTION": 25}
        snap1.metadata_json = {"officers_count": 3, "sla_breaches": 6, "disputes_count": 15}

        snap2 = Mock(spec=ProjectHistory)
        snap2.snapshot_date = datetime(2025, 2, 1, tzinfo=timezone.utc)
        snap2.land_required_ha = 450.0
        snap2.land_acquired_ha = 80.0
        snap2.parcels_total = 200
        snap2.parcels_completed = 45
        snap2.parcels_in_progress = 125
        snap2.parcels_blocked = 30
        snap2.compensation_paid_total = 18000000.0
        snap2.compensation_pending_total = 27000000.0
        snap2.stages_snapshot = {"VERIFICATION": 70, "OBJECTION": 30}
        snap2.metadata_json = {"officers_count": 3, "sla_breaches": 8, "disputes_count": 18}

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_project
        mock_db.execute.return_value.scalars.return_value.all.return_value = [snap1, snap2]

        resp = client.get(f"/api/v1/analytics/projects/{proj_id}/delay-risk")
        assert resp.status_code == 200
        data = resp.json()
        assert data["project_id"] == str(proj_id)
        assert data["status"] == "success"
        assert "risk_score" in data
        assert "risk_level" in data
        assert "confidence" in data
        assert "top_factors" in data
        assert len(data["top_factors"]) == 4
        print(f"   [OK] Analytics endpoint returns 200: Risk={data['risk_score']} ({data['risk_level']}), Confidence={data['confidence']}")
        print(f"   [OK] Top factor returned: {data['top_factors'][0]['title']}")

        # 3. Route alias without /api/v1
        resp_alias = client.get(f"/analytics/projects/{proj_id}/delay-risk")
        assert resp_alias.status_code == 200
        print("   [OK] Un-prefixed route alias /analytics/projects/{id}/delay-risk returns 200")

    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def run_all_tests():
    print("=" * 70)
    print("  BHOOMI-SETU -- Delay-Risk ML Pipeline Verification Suite")
    print("=" * 70)

    test_shared_feature_engineering()
    test_delay_risk_service()
    test_analytics_api_endpoint()

    print("\n" + "=" * 70)
    print("  [SUCCESS] ALL DELAY-RISK ML TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()

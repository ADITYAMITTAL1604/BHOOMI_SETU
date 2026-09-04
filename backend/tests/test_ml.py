"""Integration tests for Machine Learning delay risk prediction and explainability."""

from __future__ import annotations

import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ml.delay_risk_service import get_delay_risk_service
from app.ml.features import build_features, PRIMARY_MODEL_FEATURES
from app.models.enums import ProjectStatus
from app.models.project import Project


def test_ml_feature_vector_structure():
    """Verify build_features produces all 10 required features for RandomForest model."""
    sample_snapshots = [
        {
            "snapshot_date": "2025-01-01",
            "parcels_total": 50,
            "parcels_completed": 10,
            "parcels_in_progress": 38,
            "parcels_disputed": 2,
            "compensation_paid_total": 5000000.0,
            "compensation_pending_total": 2000000.0,
            "pending_parcels": 38,
            "completed_parcels": 10,
            "average_stage_days": 35.0,
            "sla_breaches": 2,
            "compensation_pending": 8,
            "rr_pending": 4,
            "possession_pending": 3,
            "processing_rate": 0.15,
        },
        {
            "snapshot_date": "2025-01-15",
            "parcels_total": 50,
            "parcels_completed": 15,
            "parcels_in_progress": 33,
            "parcels_disputed": 2,
            "compensation_paid_total": 7500000.0,
            "compensation_pending_total": 1500000.0,
            "pending_parcels": 33,
            "completed_parcels": 15,
            "average_stage_days": 32.0,
            "sla_breaches": 1,
            "compensation_pending": 5,
            "rr_pending": 3,
            "possession_pending": 2,
            "processing_rate": 0.18,
        },
    ]
    feature_dict = build_features(sample_snapshots)
    assert len(PRIMARY_MODEL_FEATURES) == 10
    for name in PRIMARY_MODEL_FEATURES:
        assert name in feature_dict, f"Missing feature: {name}"
        assert isinstance(feature_dict[name], (int, float))


def test_ml_service_inference():
    """Verify model loading, prediction calibration, and explainability fallback."""
    service = get_delay_risk_service()
    assert service.is_ready, "DelayRiskService failed to load model or imputer"

    low_risk_features = {
        "pending_parcels": 5.0,
        "completed_parcels": 80.0,
        "average_stage_days": 20.0,
        "sla_breaches": 0.0,
        "compensation_pending": 2.0,
        "rr_pending": 1.0,
        "possession_pending": 0.0,
        "processing_rate": 0.94,
        "pending_trend": -0.5,
        "rate_trend": 0.1,
    }
    low_res = service.predict_delay_risk(low_risk_features, project_id="test-low")
    assert 0.0 <= low_res["risk_score"] <= 1.0
    assert low_res["risk_level"].lower() in ("low", "medium", "high")
    assert "top_factors" in low_res
    assert len(low_res["top_factors"]) > 0

    high_risk_features = {
        "pending_parcels": 150.0,
        "completed_parcels": 5.0,
        "average_stage_days": 110.0,
        "sla_breaches": 45.0,
        "compensation_pending": 80.0,
        "rr_pending": 60.0,
        "possession_pending": 90.0,
        "processing_rate": 0.03,
        "pending_trend": 2.5,
        "rate_trend": -0.2,
    }
    high_res = service.predict_delay_risk(high_risk_features, project_id="test-high")
    assert high_res["risk_score"] > low_res["risk_score"]


def test_ml_api_delay_risk_endpoint(
    client: TestClient,
    admin_headers: dict[str, str],
    db_session: Session,
):
    """Test REST endpoint /api/v1/analytics/projects/{id}/delay-risk."""
    proj = Project(
        project_id=uuid.uuid4(),
        name="ML Endpoint API Corridor",
        type="Port",
        states=["Maharashtra"],
        districts=["Raigad"],
        land_required_ha=200.0,
        status=ProjectStatus.ACTIVE.value,
    )
    db_session.add(proj)
    db_session.commit()

    res = client.get(
        f"/api/v1/analytics/projects/{proj.project_id}/delay-risk",
        headers=admin_headers,
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert "top_factors" in data
    assert "feature_importance" in data
    assert 0.0 <= data["risk_score"] <= 1.0

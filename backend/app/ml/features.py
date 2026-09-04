"""Shared feature engineering module for BhoomiSetu delay-risk prediction.
Ensures identical feature computation between model training and online serving.
Supports both the RandomForestClassifier (10 features) and legacy XGBoost models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

# The 10 primary features expected by data/model/delay_risk_model.joblib
PRIMARY_MODEL_FEATURES = [
    "pending_parcels",
    "completed_parcels",
    "average_stage_days",
    "sla_breaches",
    "compensation_pending",
    "rr_pending",
    "possession_pending",
    "processing_rate",
    "pending_trend",
    "rate_trend",
]

# The 9 features for XGBoost model
LEGACY_MODEL_FEATURES = [
    "backlog_trend",
    "processing_rate",
    "stage_complexity",
    "district_capacity",
    "sla_breach_rate",
    "avg_days_per_stage",
    "dispute_ratio",
    "compensation_pending_ratio",
    "snapshot_count",
]

FEATURE_NAMES = PRIMARY_MODEL_FEATURES

FEATURE_LABELS: Dict[str, Dict[str, str]] = {
    # 10 Primary Model Features
    "pending_parcels": {
        "title": "Pending Parcel Backlog",
        "description_high": "High volume of parcels currently pending administrative clearance",
        "description_low": "Low volume of active pending parcels",
    },
    "completed_parcels": {
        "title": "Completed Parcel Volume",
        "description_high": "Substantial parcel acquisition completion achieved",
        "description_low": "Few parcels have reached final completion",
    },
    "average_stage_days": {
        "title": "Average Dwell Time Per Stage",
        "description_high": "Prolonged dwell time across procedural workflow stages",
        "description_low": "Swift milestone progression across stages",
    },
    "sla_breaches": {
        "title": "Regulatory SLA Breaches",
        "description_high": "Multiple workflow stages have breached statutory deadlines",
        "description_low": "Workflow stages largely proceeding within statutory time limits",
    },
    "compensation_pending": {
        "title": "Pending Compensation Funds",
        "description_high": "Significant backlog of unpaid compensation funds awaiting disbursement",
        "description_low": "Compensation payouts are disbursed promptly following award",
    },
    "rr_pending": {
        "title": "Pending R&R Cases",
        "description_high": "Rehabilitation & Resettlement verification backlog is elevated",
        "description_low": "R&R entitlements disbursed on schedule",
    },
    "possession_pending": {
        "title": "Pending Land Possession",
        "description_high": "Substantial land area awaiting physical transfer of possession",
        "description_low": "Physical land transfer proceeding smoothly",
    },
    "processing_rate": {
        "title": "Acquisition Clearance Velocity",
        "description_high": "High daily parcel clearance velocity",
        "description_low": "Clearance velocity is stagnant or below target",
    },
    "pending_trend": {
        "title": "Parcel Backlog Trajectory",
        "description_high": "Backlog volume is expanding across recent observation intervals",
        "description_low": "Backlog volume is shrinking or stable",
    },
    "rate_trend": {
        "title": "Processing Velocity Trend",
        "description_high": "Clearance speed is accelerating over time",
        "description_low": "Clearance velocity is decelerating",
    },
    # Additional Contextual Features
    "backlog_trend": {
        "title": "Backlog Expansion Rate",
        "description_high": "Pending and blocked parcel queue is growing over time",
        "description_low": "Parcel backlog is steadily clearing or stable",
    },
    "stage_complexity": {
        "title": "Workflow Stage Complexity",
        "description_high": "High proportion of parcels in legally complex stages (Objection, R&R, Award)",
        "description_low": "Parcels predominantly in early survey or final closure stages",
    },
    "district_capacity": {
        "title": "District Administrative Capacity",
        "description_high": "Adequate officer staffing relative to active parcel volume",
        "description_low": "Severe officer overload / staffing deficit in project districts",
    },
    "sla_breach_rate": {
        "title": "Statutory SLA Breach Rate",
        "description_high": "Substantial portion of active stages have breached deadlines",
        "description_low": "Low incidence of statutory timeline breaches",
    },
    "avg_days_per_stage": {
        "title": "Average Duration Per Stage",
        "description_high": "Prolonged dwell time across procedural workflow stages",
        "description_low": "Swift milestone progression across stages",
    },
    "dispute_ratio": {
        "title": "Litigation & Dispute Ratio",
        "description_high": "Elevated proportion of contested parcels or formal objections",
        "description_low": "Minimal legal challenges or ownership disputes",
    },
    "compensation_pending_ratio": {
        "title": "Pending Compensation Ratio",
        "description_high": "Significant proportion of approved funds pending payout",
        "description_low": "Compensation disbursement largely up to date",
    },
    "snapshot_count": {
        "title": "Timeline Observation Depth",
        "description_high": "Deep multi-month snapshot history available",
        "description_low": "Limited timeline observations available",
    },
}

STAGE_COMPLEXITY_WEIGHTS = {
    "PROPOSAL": 0.15,
    "IDENTIFICATION": 0.25,
    "SURVEY": 0.35,
    "VERIFICATION": 0.45,
    "NOTIFICATION": 0.50,
    "OBJECTION": 0.85,
    "AWARD": 0.80,
    "COMPENSATION": 0.90,
    "REHABILITATION_RESETTLEMENT": 0.95,
    "POSSESSION": 0.60,
    "CLOSURE": 0.10,
}

_OFFICERS_CACHE: Optional[Dict[str, int]] = None


def _get_district_officer_count(district: Optional[str]) -> int:
    """Read officer staffing count from officers dataset if available."""
    global _OFFICERS_CACHE
    if _OFFICERS_CACHE is None:
        _OFFICERS_CACHE = {}
        for candidate_path in [
            Path(__file__).resolve().parent.parent.parent.parent / "data" / "synthetic" / "officers.csv",
            Path("data/synthetic/officers.csv"),
            Path("/app/data/synthetic/officers.csv"),
        ]:
            if candidate_path.exists():
                try:
                    df = pd.read_csv(candidate_path)
                    counts = df.groupby(df["district"].str.upper())["officer_id"].count().to_dict()
                    _OFFICERS_CACHE = counts
                    break
                except Exception:
                    pass

    if district and _OFFICERS_CACHE:
        return _OFFICERS_CACHE.get(str(district).strip().upper(), 4)
    return 4


def _parse_datetime(dt_val: Any) -> Optional[datetime]:
    if dt_val is None:
        return None
    if isinstance(dt_val, datetime):
        return dt_val
    if isinstance(dt_val, str):
        try:
            return datetime.fromisoformat(dt_val.replace("Z", "+00:00"))
        except Exception:
            try:
                return pd.to_datetime(dt_val).to_pydatetime()
            except Exception:
                return None
    return None


def build_features(
    snapshots: Union[List[Dict[str, Any]], pd.DataFrame],
    project_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, float]:
    """Compute all delay-risk features from historical snapshot records.

    Produces both the 10 features for RandomForest (data/model)
    and the 9 features for XGBoost, allowing both models to operate seamlessly.
    """
    if isinstance(snapshots, pd.DataFrame):
        records = snapshots.to_dict(orient="records")
    else:
        records = list(snapshots)

    snapshot_count = len(records)
    all_keys = set(PRIMARY_MODEL_FEATURES + LEGACY_MODEL_FEATURES)
    if snapshot_count == 0:
        res = {k: 0.0 for k in all_keys}
        res["snapshot_count"] = 0
        return res

    def get_date(r):
        d = _parse_datetime(r.get("snapshot_date"))
        return d or datetime.min.replace(tzinfo=timezone.utc)

    records.sort(key=get_date)
    earliest = records[0]
    latest = records[-1]
    prev = records[-2] if snapshot_count >= 2 else earliest

    t_start = _parse_datetime(earliest.get("snapshot_date"))
    t_end = _parse_datetime(latest.get("snapshot_date"))
    if t_start and t_end and t_end > t_start:
        days_span = max(1.0, (t_end - t_start).total_seconds() / 86400.0)
    else:
        days_span = max(1.0, float(snapshot_count * 15.0))

    meta = latest.get("metadata_json") or {}

    # Basic parcel counts
    parcels_in_progress = float(latest.get("parcels_in_progress", 0))
    parcels_blocked = float(latest.get("parcels_blocked", latest.get("parcels_disputed", 0)))
    pending_parcels = float(latest.get("pending_parcels", parcels_in_progress + parcels_blocked))
    completed_parcels = float(latest.get("completed_parcels", latest.get("parcels_completed", 0)))

    # Previous interval for trends
    prev_in_progress = float(prev.get("parcels_in_progress", 0))
    prev_blocked = float(prev.get("parcels_blocked", prev.get("parcels_disputed", 0)))
    prev_pending = float(prev.get("pending_parcels", prev_in_progress + prev_blocked))
    prev_completed = float(prev.get("completed_parcels", prev.get("parcels_completed", 0)))

    # Trajectories
    earliest_backlog = float(earliest.get("parcels_in_progress", 0) + earliest.get("parcels_blocked", 0))
    latest_backlog = pending_parcels
    backlog_trend = (latest_backlog - earliest_backlog) / days_span if snapshot_count >= 2 else 0.0

    earliest_completed = float(earliest.get("parcels_completed", earliest.get("completed_parcels", 0)))
    if snapshot_count >= 2:
        processing_rate = max(0.0, (completed_parcels - earliest_completed) / days_span)
    else:
        processing_rate = completed_parcels / max(30.0, days_span)

    # Short-term trends (from Script 09)
    pending_trend = pending_parcels - prev_pending
    prev_rate = float(prev.get("processing_rate", processing_rate))
    latest_rate = float(latest.get("processing_rate", processing_rate))
    rate_trend = latest_rate - prev_rate

    # Stage complexity
    stage_complexity = 0.5
    stages_data = latest.get("stages_snapshot")
    if isinstance(stages_data, dict) and stages_data:
        total_staged = 0
        weighted_sum = 0.0
        for s_name, count in stages_data.items():
            cnt = float(count) if isinstance(count, (int, float)) else 0.0
            w = STAGE_COMPLEXITY_WEIGHTS.get(str(s_name).upper(), 0.5)
            weighted_sum += cnt * w
            total_staged += cnt
        if total_staged > 0:
            stage_complexity = round(weighted_sum / total_staged, 4)
    elif "stage_complexity" in meta:
        stage_complexity = float(meta["stage_complexity"])

    # District capacity
    first_district = None
    if project_meta and project_meta.get("districts"):
        dists = project_meta["districts"]
        first_district = dists[0] if isinstance(dists, list) and dists else None

    officers_count = meta.get("officers_count") or (project_meta or {}).get("officers_count")
    if officers_count is None:
        officers_count = _get_district_officer_count(first_district)

    active_parcels = max(1.0, pending_parcels)
    expected_officers = max(1.0, active_parcels / 40.0)
    district_capacity = round(min(1.0, max(0.05, float(officers_count) / expected_officers)), 4)

    # SLA Breaches
    sla_breaches = float(latest.get("sla_breaches") or meta.get("sla_breaches") or 0.0)
    total_active_stages = max(1.0, float(meta.get("active_stages_count", 11)))
    sla_breach_rate = min(1.0, sla_breaches / total_active_stages)

    # Average days per stage
    avg_stage_days = latest.get("average_stage_days") or meta.get("average_stage_days")
    if avg_stage_days is not None:
        average_stage_days = float(avg_stage_days)
    else:
        tot_parcels = float(latest.get("parcels_total", completed_parcels + pending_parcels or 100))
        pct = completed_parcels / max(1.0, tot_parcels)
        stages_passed = max(1.0, pct * 10.0)
        average_stage_days = min(180.0, max(10.0, (days_span * 1.5) / stages_passed))

    # Compensation Pending
    comp_pending_raw = latest.get("compensation_pending")
    if comp_pending_raw is not None:
        compensation_pending = float(comp_pending_raw)
    else:
        compensation_pending = float(latest.get("compensation_pending_total", 0.0))

    comp_paid = float(latest.get("compensation_paid_total", 0.0))
    tot_comp = comp_paid + compensation_pending
    compensation_pending_ratio = round(compensation_pending / tot_comp, 4) if tot_comp > 0 else 0.0

    # R&R Pending & Possession Pending
    rr_pending = float(latest.get("rr_pending") or meta.get("rr_pending") or round(pending_parcels * 0.25))
    possession_pending = float(latest.get("possession_pending") or meta.get("possession_pending") or round(pending_parcels * 0.15))

    # Dispute Ratio
    tot_parcels = float(latest.get("parcels_total", completed_parcels + pending_parcels or 100))
    disputes = meta.get("disputes_count")
    if disputes is not None:
        dispute_ratio = min(1.0, float(disputes) / max(1.0, tot_parcels))
    else:
        dispute_ratio = min(1.0, parcels_blocked / max(1.0, tot_parcels))

    return {
        # 10 features for data/model
        "pending_parcels": round(float(pending_parcels), 2),
        "completed_parcels": round(float(completed_parcels), 2),
        "average_stage_days": round(float(average_stage_days), 2),
        "sla_breaches": round(float(sla_breaches), 2),
        "compensation_pending": round(float(compensation_pending), 2),
        "rr_pending": round(float(rr_pending), 2),
        "possession_pending": round(float(possession_pending), 2),
        "processing_rate": round(float(processing_rate), 4),
        "pending_trend": round(float(pending_trend), 4),
        "rate_trend": round(float(rate_trend), 4),
        # Legacy XGBoost features
        "backlog_trend": round(float(backlog_trend), 4),
        "stage_complexity": round(float(stage_complexity), 4),
        "district_capacity": round(float(district_capacity), 4),
        "sla_breach_rate": round(float(sla_breach_rate), 4),
        "avg_days_per_stage": round(float(average_stage_days), 2),
        "dispute_ratio": round(float(dispute_ratio), 4),
        "compensation_pending_ratio": round(float(compensation_pending_ratio), 4),
        "snapshot_count": int(snapshot_count),
    }

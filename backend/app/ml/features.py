"""Shared feature engineering module for BhoomiSetu delay-risk prediction.
Ensures identical feature computation between model training and online serving.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

FEATURE_NAMES = [
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

FEATURE_LABELS = {
    "backlog_trend": {
        "title": "Parcel Backlog Trend",
        "description_high": "Pending and blocked parcel queue is growing over time",
        "description_low": "Parcel backlog is steadily clearing or stable",
    },
    "processing_rate": {
        "title": "Acquisition Processing Rate",
        "description_high": "High daily parcel clearance velocity",
        "description_low": "Clearance velocity is stagnant or below target",
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
        "title": "Regulatory SLA Breach Rate",
        "description_high": "Substantial portion of active acquisition stages have breached statutory deadlines",
        "description_low": "Workflow stages largely proceeding within statutory time limits",
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
        "title": "Pending Compensation Disbursement Ratio",
        "description_high": "Significant backlog of unpaid compensation funds awaiting disbursement",
        "description_low": "Compensation payouts are disbursed promptly following award",
    },
    "snapshot_count": {
        "title": "Timeline Observation Depth",
        "description_high": "Deep multi-month snapshot history available for trend analysis",
        "description_low": "Limited timeline observations available",
    },
}

# Regulatory complexity weights per stage
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
    """Compute the 9 standardized delay-risk features from historical snapshot records.

    Parameters
    ----------
    snapshots : list of dicts or pandas DataFrame
        Chronological or un-ordered list/DataFrame of project snapshot records.
        Expected keys/columns:
          - snapshot_date
          - parcels_total
          - parcels_completed
          - parcels_in_progress
          - parcels_blocked
          - compensation_paid_total
          - compensation_pending_total
          - stages_snapshot (optional dict with stage breakdown or SLA counts)
          - metadata_json (optional dict with dispute / officer / breach details)
    project_meta : dict, optional
        Project-level static metadata (e.g. land_required_ha, districts, officers count).

    Returns
    -------
    dict of {feature_name: float}
    """
    if isinstance(snapshots, pd.DataFrame):
        records = snapshots.to_dict(orient="records")
    else:
        records = list(snapshots)

    snapshot_count = len(records)
    if snapshot_count == 0:
        return {name: 0.0 for name in FEATURE_NAMES}

    # Sort records by snapshot_date ascending
    def get_date(r):
        d = _parse_datetime(r.get("snapshot_date"))
        return d or datetime.min.replace(tzinfo=timezone.utc)

    records.sort(key=get_date)
    earliest = records[0]
    latest = records[-1]

    # Time span calculation
    t_start = _parse_datetime(earliest.get("snapshot_date"))
    t_end = _parse_datetime(latest.get("snapshot_date"))
    if t_start and t_end and t_end > t_start:
        days_span = max(1.0, (t_end - t_start).total_seconds() / 86400.0)
    else:
        days_span = max(1.0, float(snapshot_count * 15.0))

    # 1. Backlog Trend
    # Backlog = in_progress + blocked
    earliest_backlog = float(earliest.get("parcels_in_progress", 0) + earliest.get("parcels_blocked", 0))
    latest_backlog = float(latest.get("parcels_in_progress", 0) + latest.get("parcels_blocked", 0))
    if snapshot_count >= 2:
        backlog_trend = (latest_backlog - earliest_backlog) / days_span
    else:
        backlog_trend = 0.0

    # 2. Processing Rate (parcels completed per day)
    earliest_completed = float(earliest.get("parcels_completed", 0))
    latest_completed = float(latest.get("parcels_completed", 0))
    if snapshot_count >= 2:
        processing_rate = max(0.0, (latest_completed - earliest_completed) / days_span)
    else:
        # Fallback approximation from latest
        processing_rate = latest_completed / max(30.0, days_span)

    # 3. Stage Complexity
    # Derived from stages_snapshot or estimated from parcel distribution
    stage_complexity = 0.5  # default baseline
    stages_data = latest.get("stages_snapshot")
    if isinstance(stages_data, dict) and stages_data:
        total_staged = 0
        weighted_sum = 0.0
        for stage_name, count in stages_data.items():
            cnt = float(count) if isinstance(count, (int, float)) else 0.0
            weight = STAGE_COMPLEXITY_WEIGHTS.get(str(stage_name).upper(), 0.5)
            weighted_sum += cnt * weight
            total_staged += cnt
        if total_staged > 0:
            stage_complexity = round(weighted_sum / total_staged, 4)
    else:
        # Check metadata or estimate from ratio of blocked to total
        meta = latest.get("metadata_json") or {}
        if "stage_complexity" in meta:
            stage_complexity = float(meta["stage_complexity"])
        else:
            # Synthetic proxy from project progress
            tot = float(latest.get("parcels_total", 100))
            comp = float(latest.get("parcels_completed", 0))
            ratio = comp / max(1.0, tot)
            # Middle stages (30% to 70% completed) usually have peak complexity (awards, R&R, disputes)
            stage_complexity = round(0.4 + 0.5 * np.sin(ratio * np.pi), 4)

    # 4. District Capacity
    # Default is ratio of available field officers to workload
    meta = latest.get("metadata_json") or {}
    officers_count = meta.get("officers_count") or (project_meta or {}).get("officers_count", 4)
    active_parcels = float(latest.get("parcels_in_progress", 50) + latest.get("parcels_blocked", 10))
    # Standard benchmark: 1 officer per 40 active parcels = 1.0 capacity
    expected_officers = max(1.0, active_parcels / 40.0)
    district_capacity = round(min(1.0, max(0.05, float(officers_count) / expected_officers)), 4)

    # 5. SLA Breach Rate
    sla_breaches = meta.get("sla_breaches") or meta.get("sla_breached_stages")
    if sla_breaches is not None:
        total_active_stages = max(1.0, float(meta.get("active_stages_count", 11)))
        sla_breach_rate = min(1.0, float(sla_breaches) / total_active_stages)
    else:
        # Proxy from parcels_blocked / active_parcels
        tot_active = max(1.0, active_parcels)
        sla_breach_rate = min(1.0, float(latest.get("parcels_blocked", 0)) / tot_active)

    # 6. Avg Days Per Stage
    avg_days = meta.get("avg_days_per_stage")
    if avg_days is not None:
        avg_days_per_stage = float(avg_days)
    else:
        # Approximate: days_span / number of distinct completed stage milestones
        tot_completed = float(latest.get("parcels_completed", 1))
        tot_parcels = float(latest.get("parcels_total", 100))
        pct = tot_completed / max(1.0, tot_parcels)
        stages_passed = max(1.0, pct * 10.0)
        avg_days_per_stage = min(180.0, max(10.0, (days_span * 1.5) / stages_passed))

    # 7. Dispute Ratio
    tot_parcels = float(latest.get("parcels_total", 100))
    disputes = meta.get("disputes_count")
    if disputes is not None:
        dispute_ratio = min(1.0, float(disputes) / max(1.0, tot_parcels))
    else:
        dispute_ratio = min(1.0, float(latest.get("parcels_blocked", 0)) / max(1.0, tot_parcels))

    # 8. Compensation Pending Ratio
    comp_paid = float(latest.get("compensation_paid_total", 0.0))
    comp_pending = float(latest.get("compensation_pending_total", 0.0))
    tot_comp = comp_paid + comp_pending
    if tot_comp > 0:
        compensation_pending_ratio = round(comp_pending / tot_comp, 4)
    else:
        compensation_pending_ratio = 0.0

    return {
        "backlog_trend": round(float(backlog_trend), 4),
        "processing_rate": round(float(processing_rate), 4),
        "stage_complexity": round(float(stage_complexity), 4),
        "district_capacity": round(float(district_capacity), 4),
        "sla_breach_rate": round(float(sla_breach_rate), 4),
        "avg_days_per_stage": round(float(avg_days_per_stage), 2),
        "dispute_ratio": round(float(dispute_ratio), 4),
        "compensation_pending_ratio": round(float(compensation_pending_ratio), 4),
        "snapshot_count": int(snapshot_count),
    }

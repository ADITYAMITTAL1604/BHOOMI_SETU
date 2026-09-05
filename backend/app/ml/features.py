"""Shared feature engineering module for BhoomiSetu delay-risk prediction.
Ensures identical feature computation between model training and online serving.
Primary model: XGBClassifier (32 normalized rate/ratio features from Phase 2c).
Backwards compatible with legacy 10-feature and 9-feature consumers.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

# The 32 normalized rate/ratio features expected by delay_risk_model.joblib (Phase 2c Winner)
PHASE2C_MODEL_FEATURES = [
    "land_required_ha",
    "target_days",
    "processing_rate",
    "processing_rate_change_1step",
    "dispute_rate",
    "dispute_rate_change_1step",
    "compensation_pct_paid",
    "rr_completed_pct",
    "rr_pending_in_progress_pct",
    "has_officer_data",
    "district_workload_ratio",
    "pending_parcels_rate",
    "completed_parcels_rate",
    "sla_breach_rate",
    "compensation_pending_rate",
    "rr_pending_rate",
    "possession_pending_rate",
    "compensation_pending_partial_rate",
    "pending_stage_0_land_identification_rate",
    "pending_stage_1_survey_mapping_rate",
    "pending_stage_2_ownership_verification_rate",
    "pending_stage_3_notification_rate",
    "pending_stage_4_objections_hearings_rate",
    "pending_stage_5_compensation_assessment_rate",
    "pending_stage_6_compensation_disbursement_rate",
    "pending_stage_7_rr_rate",
    "pending_stage_8_possession_rate",
    "pending_stage_9_closure_handover_rate",
    "sla_breaches_change_1step_rate",
    "pending_parcels_change_1step_rate",
    "sla_breaches_trend_3step_rate",
    "pending_parcels_trend_3step_rate",
]

PRIMARY_MODEL_FEATURES = PHASE2C_MODEL_FEATURES

# Legacy 10 features for backwards compatibility
LEGACY_10_FEATURES = [
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

# Legacy 9 features for initial prototype
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
    # 32 Phase 2c Normalized Features
    "land_required_ha": {
        "title": "Project Footprint (Hectares)",
        "description_high": "Large geographic footprint requiring extensive parcel aggregation",
        "description_low": "Compact geographic footprint with contained acquisition scope",
    },
    "target_days": {
        "title": "Statutory Target Duration",
        "description_high": "Extended implementation timeframe allocated for completion",
        "description_low": "Compressed statutory timeline demanding rapid procedural clearance",
    },
    "processing_rate": {
        "title": "Parcel Clearance Velocity",
        "description_high": "High daily parcel clearance velocity maintaining strong momentum",
        "description_low": "Clearance velocity is stagnant or below statutory benchmarks",
    },
    "processing_rate_change_1step": {
        "title": "Clearance Velocity Acceleration",
        "description_high": "Acquisition pace accelerated compared to previous observation",
        "description_low": "Acquisition pace decelerated compared to previous observation",
    },
    "dispute_rate": {
        "title": "Litigation & Dispute Rate",
        "description_high": "Elevated proportion of contested parcels or formal court disputes",
        "description_low": "Negligible litigation friction or ownership contestation",
    },
    "dispute_rate_change_1step": {
        "title": "Dispute Trajectory Delta",
        "description_high": "Contested parcel fraction has escalated recently",
        "description_low": "Contested parcel fraction is subsiding or resolved",
    },
    "compensation_pct_paid": {
        "title": "Compensation Disbursement Rate",
        "description_high": "High percentage of determined compensation disbursed to titleholders",
        "description_low": "Substantial compensation awards pending disbursement into bank accounts",
    },
    "rr_completed_pct": {
        "title": "R&R Resettlement Completion",
        "description_high": "Rehabilitation & Resettlement verification largely completed",
        "description_low": "Significant Rehabilitation & Resettlement caseload unresolved",
    },
    "rr_pending_in_progress_pct": {
        "title": "Active R&R Processing",
        "description_high": "High active volume undergoing statutory R&R processing",
        "description_low": "Minimal pending R&R workload currently in progress",
    },
    "has_officer_data": {
        "title": "Administrative Staffing Record",
        "description_high": "Dedicated district land acquisition officers formally assigned",
        "description_low": "Unspecified administrative staffing allocation",
    },
    "district_workload_ratio": {
        "title": "District Officer Workload",
        "description_high": "Staff capacity stretched thin relative to active parcel backlog",
        "description_low": "Adequate officer staffing capacity relative to parcel volume",
    },
    "pending_parcels_rate": {
        "title": "Pending Parcel Fraction",
        "description_high": "Major fraction of project parcels remain in pending acquisition stages",
        "description_low": "Most project parcels cleared through administrative pipeline",
    },
    "completed_parcels_rate": {
        "title": "Acquisition Progress Fraction",
        "description_high": "Substantial parcel proportion successfully acquired and vested",
        "description_low": "Early phase with modest acquired parcel proportion",
    },
    "sla_breach_rate": {
        "title": "Statutory SLA Overrun Rate",
        "description_high": "Multiple procedural workflow stages have breached statutory deadlines",
        "description_low": "Procedural milestones largely proceeding within statutory deadlines",
    },
    "compensation_pending_rate": {
        "title": "Pending Compensation Fraction",
        "description_high": "Substantial fraction of parcels awaiting compensation disbursement",
        "description_low": "Compensation disbursement largely up to date across parcels",
    },
    "rr_pending_rate": {
        "title": "Pending R&R Case Fraction",
        "description_high": "High fraction of project parcels tied to unresolved R&R claims",
        "description_low": "R&R verification backlog minimal relative to total parcels",
    },
    "possession_pending_rate": {
        "title": "Pending Land Possession Rate",
        "description_high": "Physical handover pending for significant land parcel fraction",
        "description_low": "Physical possession transfers proceeding on schedule",
    },
    "compensation_pending_partial_rate": {
        "title": "Partial Compensation Pendency",
        "description_high": "Portion of awards partially disbursed awaiting final clearance",
        "description_low": "Clean compensation disbursement without partial holdbacks",
    },
    "pending_stage_0_land_identification_rate": {
        "title": "Stage 0: Land Identification Pendency",
        "description_high": "Substantial land still in preliminary identification / proposal phase",
        "description_low": "Land identification phase successfully concluded",
    },
    "pending_stage_1_survey_mapping_rate": {
        "title": "Stage 1: Survey & Mapping Pendency",
        "description_high": "Parcels awaiting joint cadastre and boundary demarcation",
        "description_low": "Cadastral field survey and GIS mapping verified",
    },
    "pending_stage_2_ownership_verification_rate": {
        "title": "Stage 2: Title Verification Pendency",
        "description_high": "Revenue title verification and mutation records under scrutiny",
        "description_low": "Land title verification cleared without legal disputes",
    },
    "pending_stage_3_notification_rate": {
        "title": "Stage 3: Statutory Notification Pendency",
        "description_high": "Gazette publication under Section 11/19 in progress",
        "description_low": "Statutory notifications officially promulgated",
    },
    "pending_stage_4_objections_hearings_rate": {
        "title": "Stage 4: Objections & Hearings Pendency",
        "description_high": "High volume of landholder objections awaiting collector hearings",
        "description_low": "Statutory objection hearings successfully concluded",
    },
    "pending_stage_5_compensation_assessment_rate": {
        "title": "Stage 5: Award Determination Pendency",
        "description_high": "Valuation and market rate assessment undergoing determination",
        "description_low": "Statutory compensation awards officially formulated",
    },
    "pending_stage_6_compensation_disbursement_rate": {
        "title": "Stage 6: Payout Disbursement Pendency",
        "description_high": "Direct benefit transfers pending release to project affected families",
        "description_low": "Compensation payouts transferred into verified accounts",
    },
    "pending_stage_7_rr_rate": {
        "title": "Stage 7: Rehabilitation & Resettlement Pendency",
        "description_high": "Entitlement allocation and housing resettlement pending execution",
        "description_low": "R&R scheme implementation fully completed",
    },
    "pending_stage_8_possession_rate": {
        "title": "Stage 8: Land Possession Transfer Pendency",
        "description_high": "Physical encumbrance removal and possession certificates pending",
        "description_low": "Physical land possession formally vested with project authority",
    },
    "pending_stage_9_closure_handover_rate": {
        "title": "Stage 9: Revenue Record Mutation & Closure",
        "description_high": "Final revenue record updating and project handover pending",
        "description_low": "Land records mutated and final acquisition closure achieved",
    },
    "sla_breaches_change_1step_rate": {
        "title": "SLA Breach Rate Trend",
        "description_high": "New statutory timeline breaches recorded since previous snapshot",
        "description_low": "No new timeline overruns recorded in latest period",
    },
    "pending_parcels_change_1step_rate": {
        "title": "Parcel Backlog Rate Trend",
        "description_high": "Backlog rate increased over the preceding interval",
        "description_low": "Backlog rate cleared downward over the preceding interval",
    },
    "sla_breaches_trend_3step_rate": {
        "title": "Multi-Step SLA Overrun Trajectory",
        "description_high": "Persistent upward drift in statutory deadline breaches over 3 periods",
        "description_low": "Stabilized or declining procedural breach trajectory over time",
    },
    "pending_parcels_trend_3step_rate": {
        "title": "Multi-Step Backlog Trajectory",
        "description_high": "Long-term backlog accumulation across multiple observation cycles",
        "description_low": "Consistent clearing of parcel backlog over multi-cycle horizon",
    },
    # Legacy Feature Labels
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
    """Compute delay-risk features from historical snapshot records.

    Produces all 32 normalized rate/ratio features for the winning Phase 2c XGBoost model,
    while also preserving the legacy feature keys for complete backward compatibility.
    """
    if isinstance(snapshots, pd.DataFrame):
        records = snapshots.to_dict(orient="records")
    else:
        records = list(snapshots)

    snapshot_count = len(records)
    all_keys = set(PHASE2C_MODEL_FEATURES + LEGACY_10_FEATURES + LEGACY_MODEL_FEATURES)
    if snapshot_count == 0:
        res = {k: 0.0 for k in all_keys}
        res["snapshot_count"] = 0
        res["target_days"] = float((project_meta or {}).get("target_days") or 365.0)
        res["land_required_ha"] = float((project_meta or {}).get("land_required_ha") or 50.0)
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
    prev_meta = prev.get("metadata_json") or {}

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

    # Total parcels
    tot_parcels = float(latest.get("parcels_total", 0) or (completed_parcels + pending_parcels) or 100.0)
    tot_parcels = max(1.0, tot_parcels)

    # Trajectories
    earliest_backlog = float(earliest.get("parcels_in_progress", 0) + earliest.get("parcels_blocked", 0))
    latest_backlog = pending_parcels
    backlog_trend = (latest_backlog - earliest_backlog) / days_span if snapshot_count >= 2 else 0.0

    earliest_completed = float(earliest.get("parcels_completed", earliest.get("completed_parcels", 0)))
    if snapshot_count >= 2:
        processing_rate = max(0.0, (completed_parcels - earliest_completed) / days_span)
    else:
        processing_rate = completed_parcels / max(30.0, days_span)

    # Short-term trends
    pending_trend = pending_parcels - prev_pending
    prev_rate = float(prev.get("processing_rate", processing_rate))
    latest_rate = float(latest.get("processing_rate", processing_rate))
    rate_trend = latest_rate - prev_rate

    # Project meta
    land_required_ha = float(
        (project_meta or {}).get("land_required_ha")
        or latest.get("land_required_ha")
        or 50.0
    )
    target_days = float(
        (project_meta or {}).get("target_days")
        or latest.get("target_days")
        or 365.0
    )

    # Rates
    pending_parcels_rate = min(1.0, max(0.0, pending_parcels / tot_parcels))
    completed_parcels_rate = min(1.0, max(0.0, completed_parcels / tot_parcels))

    # Disputes
    disputes_count = meta.get("disputes_count")
    if disputes_count is not None:
        dispute_rate = min(1.0, max(0.0, float(disputes_count) / tot_parcels))
    else:
        dispute_rate = min(1.0, max(0.0, parcels_blocked / tot_parcels))

    prev_disputes = prev_meta.get("disputes_count")
    if prev_disputes is not None:
        prev_dispute_rate = min(1.0, max(0.0, float(prev_disputes) / max(1.0, float(prev.get("parcels_total", tot_parcels)))))
    else:
        prev_dispute_rate = min(1.0, max(0.0, prev_blocked / max(1.0, float(prev.get("parcels_total", tot_parcels)))))
    dispute_rate_change_1step = (dispute_rate - prev_dispute_rate) if snapshot_count >= 2 else 0.0

    processing_rate_change_1step = rate_trend if snapshot_count >= 2 else 0.0

    # Compensation
    comp_paid = float(latest.get("compensation_paid_total", 0.0))
    comp_pending_raw = latest.get("compensation_pending")
    if comp_pending_raw is not None:
        compensation_pending = float(comp_pending_raw)
    else:
        compensation_pending = float(latest.get("compensation_pending_total", 0.0))

    tot_comp = comp_paid + compensation_pending
    if tot_comp > 0:
        compensation_pct_paid = min(100.0, max(0.0, (comp_paid / tot_comp) * 100.0))
        compensation_pending_ratio = compensation_pending / tot_comp
    else:
        compensation_pct_paid = 50.0
        compensation_pending_ratio = 0.0

    compensation_pending_rate = min(1.0, max(0.0, compensation_pending / tot_parcels if compensation_pending <= tot_parcels else compensation_pending_ratio))
    compensation_pending_partial_rate = min(1.0, max(0.0, compensation_pending_rate * 0.4))

    # R&R & Possession
    rr_pending = float(latest.get("rr_pending") or meta.get("rr_pending") or round(pending_parcels * 0.25))
    possession_pending = float(latest.get("possession_pending") or meta.get("possession_pending") or round(pending_parcels * 0.15))

    rr_pending_rate = min(1.0, max(0.0, rr_pending / tot_parcels))
    rr_completed_pct = min(100.0, max(0.0, (1.0 - min(1.0, rr_pending_rate * 1.5)) * 100.0))
    rr_pending_in_progress_pct = min(100.0, max(0.0, rr_pending_rate * 100.0))
    possession_pending_rate = min(1.0, max(0.0, possession_pending / tot_parcels))

    # Officers and district capacity
    first_district = None
    if project_meta and project_meta.get("districts"):
        dists = project_meta["districts"]
        first_district = dists[0] if isinstance(dists, list) and dists else None

    raw_officers = meta.get("officers_count") or (project_meta or {}).get("officers_count")
    has_officer_data = 1.0 if raw_officers is not None else 0.0
    officers_count = raw_officers if raw_officers is not None else _get_district_officer_count(first_district)

    active_parcels = max(1.0, pending_parcels)
    expected_officers = max(1.0, active_parcels / 40.0)
    district_capacity = min(1.0, max(0.05, float(officers_count) / expected_officers))
    district_workload_ratio = min(5.0, max(0.1, active_parcels / max(1.0, float(officers_count) * 25.0)))

    # SLA Breaches
    sla_breaches = float(latest.get("sla_breaches") or meta.get("sla_breaches") or 0.0)
    total_active_stages = max(1.0, float(meta.get("active_stages_count", 11)))
    sla_breach_rate = min(1.0, max(0.0, sla_breaches / total_active_stages))

    # Average stage days
    avg_stage_days = latest.get("average_stage_days") or meta.get("average_stage_days")
    if avg_stage_days is not None:
        average_stage_days = float(avg_stage_days)
    else:
        pct = completed_parcels / max(1.0, tot_parcels)
        stages_passed = max(1.0, pct * 10.0)
        average_stage_days = min(180.0, max(10.0, (days_span * 1.5) / stages_passed))

    # Stage rate mappings for 10 workflow stages (0..9)
    stages_snapshot = latest.get("stages_snapshot")
    stage_rates: Dict[str, float] = {}

    stage_keywords = [
        ("pending_stage_0_land_identification_rate", ["IDENTIFICATION", "PROPOSAL"]),
        ("pending_stage_1_survey_mapping_rate", ["SURVEY", "MAPPING"]),
        ("pending_stage_2_ownership_verification_rate", ["VERIFICATION", "OWNERSHIP"]),
        ("pending_stage_3_notification_rate", ["NOTIFICATION"]),
        ("pending_stage_4_objections_hearings_rate", ["OBJECTION", "HEARINGS"]),
        ("pending_stage_5_compensation_assessment_rate", ["AWARD", "ASSESSMENT"]),
        ("pending_stage_6_compensation_disbursement_rate", ["COMPENSATION", "DISBURSEMENT"]),
        ("pending_stage_7_rr_rate", ["REHABILITATION", "RESETTLEMENT", "RR"]),
        ("pending_stage_8_possession_rate", ["POSSESSION"]),
        ("pending_stage_9_closure_handover_rate", ["CLOSURE", "HANDOVER"]),
    ]

    if isinstance(stages_snapshot, dict) and stages_snapshot:
        for feat_key, kw_list in stage_keywords:
            matched_count = 0.0
            for s_name, s_count in stages_snapshot.items():
                s_str = str(s_name).upper()
                if any(kw in s_str for kw in kw_list):
                    matched_count += float(s_count) if isinstance(s_count, (int, float)) else 0.0
            stage_rates[feat_key] = min(1.0, max(0.0, matched_count / tot_parcels))
    else:
        # Balanced baseline distribution based on pending parcels rate
        base_rate = pending_parcels_rate / 10.0
        for feat_key, _ in stage_keywords:
            stage_rates[feat_key] = min(1.0, max(0.0, base_rate))

    # Stage complexity
    stage_complexity = 0.5
    if isinstance(stages_snapshot, dict) and stages_snapshot:
        total_staged = 0
        weighted_sum = 0.0
        for s_name, count in stages_snapshot.items():
            cnt = float(count) if isinstance(count, (int, float)) else 0.0
            w = STAGE_COMPLEXITY_WEIGHTS.get(str(s_name).upper(), 0.5)
            weighted_sum += cnt * w
            total_staged += cnt
        if total_staged > 0:
            stage_complexity = weighted_sum / total_staged
    elif "stage_complexity" in meta:
        stage_complexity = float(meta["stage_complexity"])

    # Trend calculations
    prev_sla = float(prev.get("sla_breaches") or prev_meta.get("sla_breaches") or 0.0)
    sla_breaches_change_1step_rate = (sla_breaches - prev_sla) / tot_parcels if snapshot_count >= 2 else 0.0
    pending_parcels_change_1step_rate = (pending_parcels - prev_pending) / tot_parcels if snapshot_count >= 2 else 0.0

    if snapshot_count >= 3:
        s3 = records[-3]
        s3_meta = s3.get("metadata_json") or {}
        s3_sla = float(s3.get("sla_breaches") or s3_meta.get("sla_breaches") or 0.0)
        s3_pending = float(s3.get("pending_parcels", s3.get("parcels_in_progress", 0) + s3.get("parcels_blocked", 0)))
        sla_breaches_trend_3step_rate = (sla_breaches - s3_sla) / (2.0 * tot_parcels)
        pending_parcels_trend_3step_rate = (pending_parcels - s3_pending) / (2.0 * tot_parcels)
    elif snapshot_count >= 2:
        sla_breaches_trend_3step_rate = sla_breaches_change_1step_rate
        pending_parcels_trend_3step_rate = pending_parcels_change_1step_rate
    else:
        sla_breaches_trend_3step_rate = 0.0
        pending_parcels_trend_3step_rate = 0.0

    return {
        # 32 Phase 2c Model Features
        "land_required_ha": round(float(land_required_ha), 2),
        "target_days": round(float(target_days), 1),
        "processing_rate": round(float(processing_rate), 4),
        "processing_rate_change_1step": round(float(processing_rate_change_1step), 4),
        "dispute_rate": round(float(dispute_rate), 4),
        "dispute_rate_change_1step": round(float(dispute_rate_change_1step), 4),
        "compensation_pct_paid": round(float(compensation_pct_paid), 2),
        "rr_completed_pct": round(float(rr_completed_pct), 2),
        "rr_pending_in_progress_pct": round(float(rr_pending_in_progress_pct), 2),
        "has_officer_data": round(float(has_officer_data), 1),
        "district_workload_ratio": round(float(district_workload_ratio), 4),
        "pending_parcels_rate": round(float(pending_parcels_rate), 4),
        "completed_parcels_rate": round(float(completed_parcels_rate), 4),
        "sla_breach_rate": round(float(sla_breach_rate), 4),
        "compensation_pending_rate": round(float(compensation_pending_rate), 4),
        "rr_pending_rate": round(float(rr_pending_rate), 4),
        "possession_pending_rate": round(float(possession_pending_rate), 4),
        "compensation_pending_partial_rate": round(float(compensation_pending_partial_rate), 4),
        **{k: round(float(v), 4) for k, v in stage_rates.items()},
        "sla_breaches_change_1step_rate": round(float(sla_breaches_change_1step_rate), 4),
        "pending_parcels_change_1step_rate": round(float(pending_parcels_change_1step_rate), 4),
        "sla_breaches_trend_3step_rate": round(float(sla_breaches_trend_3step_rate), 4),
        "pending_parcels_trend_3step_rate": round(float(pending_parcels_trend_3step_rate), 4),
        # Legacy 10 features
        "pending_parcels": round(float(pending_parcels), 2),
        "completed_parcels": round(float(completed_parcels), 2),
        "average_stage_days": round(float(average_stage_days), 2),
        "sla_breaches": round(float(sla_breaches), 2),
        "compensation_pending": round(float(compensation_pending), 2),
        "rr_pending": round(float(rr_pending), 2),
        "possession_pending": round(float(possession_pending), 2),
        "pending_trend": round(float(pending_trend), 4),
        "rate_trend": round(float(rate_trend), 4),
        # Legacy 9 features
        "backlog_trend": round(float(backlog_trend), 4),
        "stage_complexity": round(float(stage_complexity), 4),
        "district_capacity": round(float(district_capacity), 4),
        "avg_days_per_stage": round(float(average_stage_days), 2),
        "dispute_ratio": round(float(dispute_rate), 4),
        "compensation_pending_ratio": round(float(compensation_pending_ratio), 4),
        "snapshot_count": int(snapshot_count),
    }

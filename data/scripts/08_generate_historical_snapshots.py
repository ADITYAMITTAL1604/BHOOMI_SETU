"""
BHOOMISETU - Script 8: Generate Historical Snapshots
Creates time series data for ML training.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

BASE_SYNTHETIC = "D:/data/synthetic"

print("=" * 70)
print("BHOOMISETU - Script 8: Generate Historical Snapshots")
print("=" * 70)

# ============================================================================
# LOAD DATA
# ============================================================================
projects = pd.read_csv(f"{BASE_SYNTHETIC}/projects.csv")
personalities = pd.read_csv(f"{BASE_SYNTHETIC}/project_personalities.csv").set_index("project_id")["personality"].to_dict()
links = pd.read_csv(f"{BASE_SYNTHETIC}/project_parcel_links.csv")
parcel_counts = links.groupby("project_id").size().to_dict()

print(f"✅ Loaded {len(projects)} projects")

# ============================================================================
# TREND PARAMETERS BY PERSONALITY
# ============================================================================
TREND = {
    "smooth": {
        "start_pending_frac": 0.6,
        "monthly_change": -0.10,
        "processing_base": 0.15,
        "processing_noise": 0.02
    },
    "ownership_stuck": {
        "start_pending_frac": 0.85,
        "monthly_change": +0.04,
        "processing_base": 0.06,
        "processing_noise": 0.03
    },
    "compensation_stuck": {
        "start_pending_frac": 0.75,
        "monthly_change": +0.03,
        "processing_base": 0.08,
        "processing_noise": 0.02
    },
    "rr_stuck": {
        "start_pending_frac": 0.70,
        "monthly_change": +0.02,
        "processing_base": 0.09,
        "processing_noise": 0.02
    },
    "legal_dispute": {
        "start_pending_frac": 0.85,
        "monthly_change": +0.06,
        "processing_base": 0.05,
        "processing_noise": 0.04
    }
}

np.random.seed(21)

start_date = datetime(2024, 6, 1)
end_date = datetime(2025, 9, 1)
snapshot_dates = pd.date_range(start_date, end_date, freq="15D")

print(f"✅ Generating {len(snapshot_dates)} snapshots per project (bi-weekly)")

# ============================================================================
# GENERATE SNAPSHOTS
# ============================================================================
snapshots = []

for _, proj in projects.iterrows():
    pid = proj["project_id"]
    total_parcels = parcel_counts.get(pid, 50)
    personality = personalities.get(pid, "smooth")
    trend = TREND[personality]

    pending_frac = trend["start_pending_frac"]
    processing_rate = trend["processing_base"] + np.random.normal(0, 0.02)
    processing_rate = max(0.01, min(0.4, processing_rate))

    for date in snapshot_dates:
        # Random walk with drift
        pending_frac += trend["monthly_change"] / 2 + np.random.normal(0, 0.015)
        pending_frac = min(max(pending_frac, 0.05), 0.98)

        processing_rate += np.random.normal(0, trend["processing_noise"])
        processing_rate = max(0.01, min(0.4, processing_rate))

        pending = int(total_parcels * pending_frac)
        completed = total_parcels - pending

        snapshots.append({
            "project_id": pid,
            "snapshot_date": date.date().isoformat(),
            "pending_parcels": pending,
            "completed_parcels": completed,
            "average_stage_days": round(np.random.uniform(15, 90), 1),
            "sla_breaches": int(pending * np.random.uniform(0.1, 0.6)),
            "compensation_pending": int(pending * np.random.uniform(0.2, 0.7)),
            "rr_pending": int(pending * np.random.uniform(0.1, 0.4)),
            "possession_pending": int(pending * np.random.uniform(0.1, 0.3)),
            "processing_rate": round(processing_rate, 3),
            "data_source": "synthetic"
        })

# ============================================================================
# SAVE
# ============================================================================
df = pd.DataFrame(snapshots)
df.to_csv(f"{BASE_SYNTHETIC}/project_history_snapshots.csv", index=False)

print(f"\n✅ Generated {len(df)} snapshots")
print(f"   Date range: {snapshot_dates.min().date()} to {snapshot_dates.max().date()}")
print(f"   Projects: {df['project_id'].nunique()}")

# Show sample trend
for personality in ["smooth", "legal_dispute"]:
    sample_projects = [pid for pid, p in personalities.items() if p == personality]
    if sample_projects:
        sample_data = df[df["project_id"] == sample_projects[0]]
        print(f"\n  Sample trend ({personality}) — {sample_projects[0]}:")
        print(f"    Start pending: {sample_data['pending_parcels'].iloc[0]}")
        print(f"    End pending:   {sample_data['pending_parcels'].iloc[-1]}")
        print(f"    Avg rate:      {sample_data['processing_rate'].mean():.3f}")

print("\n" + "=" * 70)
print("✅ SCRIPT 8 COMPLETE!")
print("=" * 70)

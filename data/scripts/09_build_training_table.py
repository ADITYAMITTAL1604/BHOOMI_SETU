"""
BHOOMISETU - Script 9: Build ML Training Table
Creates supervised learning dataset with labels.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

BASE_SYNTHETIC = "D:/data/synthetic"
BASE_MODEL = "D:/data/model"

Path(BASE_MODEL).mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("BHOOMISETU - Script 9: Build ML Training Table")
print("=" * 70)

# ============================================================================
# LOAD DATA
# ============================================================================
df = pd.read_csv(f"{BASE_SYNTHETIC}/project_history_snapshots.csv")
df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
df = df.sort_values(["project_id", "snapshot_date"]).reset_index(drop=True)

print(f"✅ Loaded {len(df)} snapshots")

# ============================================================================
# CREATE TRAINING TABLE
# ============================================================================
rows = []
np.random.seed(42)

for pid, group in df.groupby("project_id"):
    group = group.reset_index(drop=True)

    for i in range(len(group) - 2):  # Need 2 steps ahead (~30 days)
        current = group.iloc[i]
        future = group.iloc[i + 2]

        # Features: current state + trend
        prev = group.iloc[i - 1] if i > 0 else current
        pending_trend = current["pending_parcels"] - prev["pending_parcels"]
        rate_trend = current["processing_rate"] - prev["processing_rate"]

        # Label: elevated risk if pending increases AND rate decreases
        pending_worsened = future["pending_parcels"] > current["pending_parcels"] * 1.02
        rate_worsened = future["processing_rate"] < current["processing_rate"] * 0.95
        elevated_risk = int(pending_worsened and rate_worsened)

        rows.append({
            "project_id": pid,
            "snapshot_date": current["snapshot_date"],
            "pending_parcels": current["pending_parcels"],
            "completed_parcels": current["completed_parcels"],
            "average_stage_days": current["average_stage_days"],
            "sla_breaches": current["sla_breaches"],
            "compensation_pending": current["compensation_pending"],
            "rr_pending": current["rr_pending"],
            "possession_pending": current["possession_pending"],
            "processing_rate": current["processing_rate"],
            "pending_trend": pending_trend,
            "rate_trend": rate_trend,
            "elevated_risk_next_30d": elevated_risk,
            "data_source": "synthetic"
        })

train_table = pd.DataFrame(rows)

# Introduce 3% missing values (realism)
noise_cols = ["average_stage_days", "compensation_pending"]
for col in noise_cols:
    mask = np.random.rand(len(train_table)) < 0.03
    train_table.loc[mask, col] = np.nan

# ============================================================================
# SAVE
# ============================================================================
train_table.to_csv(f"{BASE_MODEL}/project_history_training_table.csv", index=False)

print(f"✅ Training table: {len(train_table)} rows")
print(f"   Features: {[c for c in train_table.columns if c not in ['project_id', 'snapshot_date', 'elevated_risk_next_30d', 'data_source']]}")
print(f"\nTarget distribution:")
print(train_table["elevated_risk_next_30d"].value_counts(normalize=True).to_string())
print(f"\nMissing values:")
print(train_table.isnull().sum()[train_table.isnull().sum() > 0].to_string())

print("\nFeature summary:")
print(train_table[["pending_parcels", "processing_rate", "sla_breaches", "pending_trend", "rate_trend"]].describe().round(3).to_string())

print("\n" + "=" * 70)
print("✅ SCRIPT 9 COMPLETE!")
print("=" * 70)

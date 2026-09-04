"""
BHOOMISETU - Script 5: Generate Lifecycle Events (The Heart of the System)
Creates realistic acquisition stage progression with project personalities.
This is where the bottleneck patterns are injected.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

BASE_SYNTHETIC = "D:/data/synthetic"

print("=" * 70)
print("BHOOMISETU - Script 5: Generate Lifecycle Events")
print("=" * 70)

# ============================================================================
# CONFIGURATION
# ============================================================================
STAGES = [
    "Land Identification",
    "Survey/Parcel Mapping",
    "Ownership Verification",
    "Notification",
    "Objections/Hearings",
    "Compensation Assessment",
    "Compensation Disbursement",
    "Rehabilitation & Resettlement",
    "Possession",
    "Closure/Handover"
]

SLA_DAYS = {
    "Land Identification": 15,
    "Survey/Parcel Mapping": 30,
    "Ownership Verification": 45,
    "Notification": 20,
    "Objections/Hearings": 30,
    "Compensation Assessment": 40,
    "Compensation Disbursement": 30,
    "Rehabilitation & Resettlement": 60,
    "Possession": 15,
    "Closure/Handover": 10
}

# ============================================================================
# PROJECT PERSONALITIES - Creates realistic bottleneck patterns
# ============================================================================
PERSONALITIES = {
    "smooth": {
        "description": "Fast processing, few delays",
        "bottleneck_stage": None,
        "delay_multiplier": 0.8,
        "weight": 0.25,
        "dispute_prob": 0.05
    },
    "ownership_stuck": {
        "description": "Ownership verification bottleneck (missing records, disputes)",
        "bottleneck_stage": "Ownership Verification",
        "delay_multiplier": 2.8,
        "weight": 0.25,
        "dispute_prob": 0.30
    },
    "compensation_stuck": {
        "description": "Compensation disbursement bottleneck (cash flow issues)",
        "bottleneck_stage": "Compensation Disbursement",
        "delay_multiplier": 2.4,
        "weight": 0.20,
        "dispute_prob": 0.15
    },
    "rr_stuck": {
        "description": "Rehabilitation & Resettlement bottleneck",
        "bottleneck_stage": "Rehabilitation & Resettlement",
        "delay_multiplier": 2.2,
        "weight": 0.15,
        "dispute_prob": 0.10
    },
    "legal_dispute": {
        "description": "Legal disputes bottleneck (court cases, objections)",
        "bottleneck_stage": "Objections/Hearings",
        "delay_multiplier": 3.2,
        "weight": 0.15,
        "dispute_prob": 0.45
    }
}

# ============================================================================
# LOAD DATA
# ============================================================================
projects = pd.read_csv(f"{BASE_SYNTHETIC}/projects.csv")
links = pd.read_csv(f"{BASE_SYNTHETIC}/project_parcel_links.csv")

print(f"✅ Loaded {len(projects)} projects, {len(links)} parcel links")

# ============================================================================
# ASSIGN PERSONALITIES
# ============================================================================
np.random.seed(7)
names_list, weights_list = zip(*[(k, v["weight"]) for k, v in PERSONALITIES.items()])
project_personality = {
    pid: np.random.choice(names_list, p=weights_list)
    for pid in projects["project_id"]
}

personality_df = pd.DataFrame([
    {"project_id": k, "personality": v, "description": PERSONALITIES[v]["description"]}
    for k, v in project_personality.items()
])
personality_df.to_csv(f"{BASE_SYNTHETIC}/project_personalities.csv", index=False)
print(f"✅ Assigned personalities to {len(project_personality)} projects")
print(f"   Distribution: {personality_df['personality'].value_counts().to_dict()}")

# ============================================================================
# GENERATE LIFECYCLE EVENTS
# ============================================================================
records = []
base_date = datetime(2024, 1, 1)
np.random.seed(7)

# Track parcels with disputes for later use
dispute_parcels = []

for idx, row in links.iterrows():
    project_id, parcel_id = row["project_id"], row["parcel_id"]
    personality_name = project_personality.get(project_id, "smooth")
    personality = PERSONALITIES[personality_name]

    # Determine how far along this parcel is (not all at same stage)
    max_stage_idx = np.random.randint(0, len(STAGES))
    current_date = base_date + timedelta(days=np.random.randint(0, 90))

    # Check if this parcel should have a dispute
    has_dispute = np.random.rand() < personality["dispute_prob"]
    if has_dispute:
        dispute_parcels.append(parcel_id)

    for stage_idx in range(max_stage_idx + 1):
        stage = STAGES[stage_idx]
        sla = SLA_DAYS[stage]

        # Apply delay multiplier if this stage is the bottleneck
        multiplier = personality["delay_multiplier"] if stage == personality["bottleneck_stage"] else 1.0

        # Add realistic noise (log-normal distribution)
        duration = max(1, int(np.random.lognormal(
            mean=np.log(max(1, sla * multiplier)),
            sigma=0.3
        )))

        stage_start = current_date
        is_current = (stage_idx == max_stage_idx)

        if is_current:
            stage_completion = None
            days_in_stage = (datetime(2025, 9, 1) - stage_start).days
        else:
            stage_completion = stage_start + timedelta(days=duration)
            days_in_stage = duration

        records.append({
            "parcel_id": parcel_id,
            "project_id": project_id,
            "stage": stage,
            "stage_order": stage_idx,
            "stage_start_date": stage_start.date().isoformat(),
            "stage_target_date": (stage_start + timedelta(days=sla)).date().isoformat(),
            "stage_completion_date": stage_completion.date().isoformat() if stage_completion else None,
            "days_in_stage": days_in_stage,
            "sla_days": sla,
            "sla_breach": int(days_in_stage > sla),
            "is_current_stage": int(is_current),
            "data_source": "synthetic"
        })

        if stage_completion:
            current_date = stage_completion

    if idx % 500 == 0:
        print(f"  Processed {idx}/{len(links)} parcels...")

# ============================================================================
# SAVE
# ============================================================================
df = pd.DataFrame(records)
df.to_csv(f"{BASE_SYNTHETIC}/parcel_lifecycle_events.csv", index=False)

# Current status snapshot
current_status = df[df["is_current_stage"] == 1].copy()
current_status.to_csv(f"{BASE_SYNTHETIC}/parcel_current_status.csv", index=False)

print(f"\n✅ Generated {len(df)} lifecycle stage records")
print(f"✅ Current status for {len(current_status)} parcels")

# SLA breach report
print("\nSLA Breach Rate by Stage:")
breach_report = df.groupby("stage")["sla_breach"].mean().round(2)
for stage, rate in breach_report.items():
    marker = "🔴" if rate > 0.5 else ("🟡" if rate > 0.3 else "🟢")
    print(f"  {marker} {stage}: {rate:.0%}")

# Save dispute parcels list for later
unique_disputes = list(set(dispute_parcels))
pd.DataFrame({"parcel_id": unique_disputes}).to_csv(
    f"{BASE_SYNTHETIC}/dispute_parcels_list.csv", index=False
)
print(f"\n✅ Identified {len(unique_disputes)} parcels with disputes")

print("\n" + "=" * 70)
print("✅ SCRIPT 5 COMPLETE!")
print("=" * 70)

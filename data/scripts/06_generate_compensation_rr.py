"""
BHOOMISETU - Script 6: Generate Compensation, R&R, and Disputes
Creates realistic financial and rehabilitation records.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

BASE_SYNTHETIC = "D:/data/synthetic"

print("=" * 70)
print("BHOOMISETU - Script 6: Compensation, R&R, and Disputes")
print("=" * 70)

# ============================================================================
# LOAD DATA
# ============================================================================
status = pd.read_csv(f"{BASE_SYNTHETIC}/parcel_current_status.csv")
personalities = pd.read_csv(f"{BASE_SYNTHETIC}/project_personalities.csv").set_index("project_id")["personality"].to_dict()
dispute_list = pd.read_csv(f"{BASE_SYNTHETIC}/dispute_parcels_list.csv")["parcel_id"].tolist()
dispute_set = set(dispute_list)

print(f"✅ Loaded {len(status)} parcels, {len(personalities)} project personalities")
print(f"✅ {len(dispute_list)} parcels flagged for disputes")

STAGE_ORDER = {stage: i for i, stage in enumerate([
    "Land Identification", "Survey/Parcel Mapping", "Ownership Verification",
    "Notification", "Objections/Hearings", "Compensation Assessment",
    "Compensation Disbursement", "Rehabilitation & Resettlement",
    "Possession", "Closure/Handover"
])}

np.random.seed(11)

# ============================================================================
# GENERATE RECORDS
# ============================================================================
comp_records = []
rr_records = []
dispute_records = []

for _, row in status.iterrows():
    parcel_id = row["parcel_id"]
    project_id = row["project_id"]
    stage = row["stage"]
    rank = STAGE_ORDER.get(stage, 0)

    # --- Compensation ---
    if rank >= STAGE_ORDER["Compensation Assessment"]:
        assessed = round(np.random.uniform(500000, 5000000), 2)
        approved = round(assessed * np.random.uniform(0.85, 1.0), 2)
        paid = 0.0
        payment_status = "pending"
        payment_date = None

        if rank >= STAGE_ORDER["Compensation Disbursement"]:
            paid_fraction = np.random.choice([1.0, 0.5, 0.0], p=[0.6, 0.25, 0.15])
            paid = round(approved * paid_fraction, 2)
            payment_status = "paid" if paid_fraction == 1.0 else ("partial" if paid_fraction > 0 else "pending")
            if paid_fraction > 0:
                payment_date = (datetime(2024, 1, 1) + timedelta(days=int(np.random.randint(60, 500)))).date().isoformat()

        comp_records.append({
            "parcel_id": parcel_id,
            "project_id": project_id,
            "assessed_amount": assessed,
            "approved_amount": approved,
            "paid_amount": paid,
            "payment_date": payment_date,
            "payment_status": payment_status,
            "data_source": "synthetic"
        })

    # --- R&R Families ---
    if rank >= STAGE_ORDER["Rehabilitation & Resettlement"]:
        n_families = np.random.randint(1, 4)
        for f in range(n_families):
            rr_records.append({
                "family_id": f"FAM-{parcel_id}-{f}",
                "parcel_id": parcel_id,
                "project_id": project_id,
                "affected": True,
                "displaced": bool(np.random.rand() < 0.4),
                "rr_eligibility": "eligible",
                "rr_status": np.random.choice(["completed", "in_progress", "pending"], p=[0.5, 0.3, 0.2]),
                "benefit_type": np.random.choice(["housing", "cash", "livelihood_support"]),
                "benefit_status": np.random.choice(["disbursed", "pending"], p=[0.6, 0.4]),
                "data_source": "synthetic"
            })

    # --- Disputes ---
    if parcel_id in dispute_set:
        case_date = (datetime(2024, 1, 1) + timedelta(days=int(np.random.randint(0, 400)))).date()
        days_pending = (datetime(2025, 9, 1).date() - case_date).days
        dispute_records.append({
            "parcel_id": parcel_id,
            "project_id": project_id,
            "dispute_type": np.random.choice(["ownership_claim", "compensation_amount", "boundary_dispute", "inheritance"]),
            "dispute_status": np.random.choice(["open", "under_review", "resolved"], p=[0.5, 0.3, 0.2]),
            "case_date": case_date.isoformat(),
            "days_pending": max(0, days_pending),
            "administrative_impact": np.random.choice(["blocks_possession", "blocks_payment", "informational"], p=[0.4, 0.4, 0.2]),
            "data_source": "synthetic"
        })

# ============================================================================
# SAVE
# ============================================================================
pd.DataFrame(comp_records).to_csv(f"{BASE_SYNTHETIC}/compensation.csv", index=False)
pd.DataFrame(rr_records).to_csv(f"{BASE_SYNTHETIC}/rehabilitation_resettlement.csv", index=False)
pd.DataFrame(dispute_records).to_csv(f"{BASE_SYNTHETIC}/disputes.csv", index=False)

print(f"\n✅ Compensation records: {len(comp_records)}")
print(f"✅ R&R family records: {len(rr_records)}")
print(f"✅ Dispute records: {len(dispute_records)}")

# Summary stats
comp_df = pd.DataFrame(comp_records)
if len(comp_df) > 0:
    print(f"\nCompensation Summary:")
    print(f"  Total assessed:  ₹{comp_df['assessed_amount'].sum():>15,.2f}")
    print(f"  Total approved:  ₹{comp_df['approved_amount'].sum():>15,.2f}")
    print(f"  Total paid:      ₹{comp_df['paid_amount'].sum():>15,.2f}")
    print(f"  Avg assessment:  ₹{comp_df['assessed_amount'].mean():>15,.2f}")
    print(f"\n  Payment Status:")
    print(comp_df['payment_status'].value_counts().to_string())

disp_df = pd.DataFrame(dispute_records)
if len(disp_df) > 0:
    print(f"\nDispute Summary:")
    print(disp_df['dispute_type'].value_counts().to_string())
    print(f"\n  Status:")
    print(disp_df['dispute_status'].value_counts().to_string())

print("\n" + "=" * 70)
print("✅ SCRIPT 6 COMPLETE!")
print("=" * 70)

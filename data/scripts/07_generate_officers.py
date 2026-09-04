"""
BHOOMISETU - Script 7: Generate Officers and Workload
Creates realistic officer caseloads.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from faker import Faker
from pathlib import Path

BASE_SYNTHETIC = "D:/data/synthetic"
BASE_PROCESSED = "D:/data/processed"

print("=" * 70)
print("BHOOMISETU - Script 7: Generate Officers")
print("=" * 70)

fake = Faker("en_IN")
np.random.seed(3)

# Try to get district names from parcels or processed data
try:
    parcels = pd.read_csv(f"{BASE_SYNTHETIC}/projects.csv")
    # Get unique districts from parcel data
    parcels_geo = pd.read_json(f"{BASE_SYNTHETIC}/parcels_geometry.geojson")
except Exception:
    pass

# Get district names from the processed districts GeoJSON
try:
    import geopandas as gpd
    districts_gdf = gpd.read_file(f"{BASE_PROCESSED}/districts.geojson")
    # Find district name column
    dist_col = None
    for col in districts_gdf.columns:
        if 'dist' in col.lower() or 'name' in col.lower():
            if districts_gdf[col].dtype == 'object':
                dist_col = col
                break
    if dist_col:
        district_names = districts_gdf[dist_col].dropna().unique().tolist()[:20]  # Limit to 20
    else:
        district_names = ["Lucknow", "Kanpur", "Agra", "Varanasi", "Allahabad",
                          "Meerut", "Gorakhpur", "Bareilly", "Ghaziabad", "Moradabad"]
except Exception:
    district_names = ["Lucknow", "Kanpur", "Agra", "Varanasi", "Allahabad",
                      "Meerut", "Gorakhpur", "Bareilly", "Ghaziabad", "Moradabad"]

print(f"✅ Generating officers for {len(district_names)} districts")

roles = [
    "District Land Acquisition Officer",
    "Tehsildar",
    "Compensation Officer",
    "R&R Officer"
]

officers = []
for district in district_names:
    for role in roles:
        assigned = int(np.random.randint(30, 200))
        completed = int(assigned * np.random.uniform(0.4, 0.9))
        officers.append({
            "officer_id": f"OFC-{fake.unique.random_number(digits=5)}",
            "name": fake.name(),
            "district": district,
            "role": role,
            "assigned_cases": assigned,
            "completed_cases": completed,
            "pending_cases": assigned - completed,
            "average_processing_days": round(np.random.uniform(10, 90), 1),
            "sla_breaches": int(np.random.poisson(max(1, assigned * 0.15))),
            "data_source": "synthetic"
        })

officers_df = pd.DataFrame(officers)
officers_df.to_csv(f"{BASE_SYNTHETIC}/officers.csv", index=False)

print(f"✅ Generated {len(officers)} officers")
print(f"\nOfficers by Role:")
print(officers_df['role'].value_counts().to_string())
print(f"\nAvg caseload: {officers_df['assigned_cases'].mean():.0f}")
print(f"Avg completion rate: {(officers_df['completed_cases'] / officers_df['assigned_cases']).mean():.1%}")

print("\n" + "=" * 70)
print("✅ SCRIPT 7 COMPLETE!")
print("=" * 70)

"""
BHOOMISETU - Script 4: Generate Projects from Road Corridors
Creates projects by buffering road segments and intersecting with parcels.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import geopandas as gpd
import numpy as np
import pandas as pd
from faker import Faker
from pathlib import Path

BASE_PROCESSED = "D:/data/processed"
BASE_SYNTHETIC = "D:/data/synthetic"

print("=" * 70)
print("BHOOMISETU - Script 4: Generate Projects")
print("=" * 70)

fake = Faker("en_IN")
np.random.seed(42)

# Load data
roads = gpd.read_file(f"{BASE_PROCESSED}/roads.geojson")
parcels = gpd.read_file(f"{BASE_SYNTHETIC}/parcels_geometry.geojson")

print(f"✅ Loaded {len(roads)} roads, {len(parcels)} parcels")

# Reproject to metric CRS for buffering
roads_m = roads.to_crs(epsg=32644)   # UTM zone 44N (covers UP)
parcels_m = parcels.to_crs(epsg=32644)

# Project configuration
N_PROJECTS = 15
project_types = [
    "Highway Expansion Project",
    "Railway Corridor Project",
    "Irrigation Canal Project",
    "Industrial Corridor Project",
    "Power Transmission Line Project",
    "Urban Infrastructure Project",
    "Rural Connectivity Project"
]

# Sample roads (prefer longer ones)
roads_m['length'] = roads_m.geometry.length
if len(roads_m) > N_PROJECTS * 2:
    sample_roads = roads_m.nlargest(N_PROJECTS * 2, 'length').sample(N_PROJECTS, random_state=42)
elif len(roads_m) > N_PROJECTS:
    sample_roads = roads_m.sample(N_PROJECTS, random_state=42)
else:
    sample_roads = roads_m

print(f"✅ Sampled {len(sample_roads)} roads for project corridors")

projects = []
project_parcel_links = []

# Build spatial index for parcels
parcels_sindex = parcels_m.sindex

for i, (_, road) in enumerate(sample_roads.iterrows()):
    project_id = f"PRJ-{i+1:03d}"
    buffer_m = int(np.random.choice([50, 75, 100, 150, 200, 300]))

    corridor = road.geometry.buffer(buffer_m)

    # Use spatial index for fast intersection
    possible_matches_idx = list(parcels_sindex.intersection(corridor.bounds))
    if len(possible_matches_idx) == 0:
        continue
    possible_matches = parcels_m.iloc[possible_matches_idx]
    affected = possible_matches[possible_matches.geometry.intersects(corridor)]

    if len(affected) < 3:
        # Try larger buffer
        corridor = road.geometry.buffer(buffer_m * 3)
        possible_matches_idx = list(parcels_sindex.intersection(corridor.bounds))
        if len(possible_matches_idx) == 0:
            continue
        possible_matches = parcels_m.iloc[possible_matches_idx]
        affected = possible_matches[possible_matches.geometry.intersects(corridor)]
        buffer_m = buffer_m * 3

    if len(affected) < 2:
        continue

    # Get project name
    city = fake.city()
    ptype = np.random.choice(project_types)
    name = f"{city} {ptype}"

    projects.append({
        "project_id": project_id,
        "name": name,
        "type": ptype,
        "state": "Uttar Pradesh",
        "corridor_width_m": buffer_m,
        "land_required_ha": round(len(affected) * 0.4, 2),
        "target_days": int(np.random.choice([180, 270, 365, 540, 730])),
        "total_parcels": min(len(affected), 200),
        "data_source": "synthetic"
    })

    for pid in affected["parcel_id"].tolist()[:200]:  # Cap parcels per project
        project_parcel_links.append({
            "project_id": project_id,
            "parcel_id": pid
        })

    print(f"  {project_id}: {name} — {len(affected)} parcels affected (saved {min(len(affected), 200)})")

# If we got fewer than 15 projects, create some from random parcel clusters
if len(projects) < N_PROJECTS:
    print(f"\n  ⚠️ Only {len(projects)} road-based projects. Creating supplemental projects...")
    remaining = N_PROJECTS - len(projects)
    # Group parcels by district
    districts = parcels["district"].unique()
    for d_idx, district in enumerate(districts[:remaining]):
        project_id = f"PRJ-{len(projects) + d_idx + 1:03d}"
        d_parcels = parcels[parcels["district"] == district]
        sample_size = min(len(d_parcels), np.random.randint(20, 100))
        sampled = d_parcels.sample(n=sample_size, random_state=42 + d_idx)

        ptype = np.random.choice(project_types)
        name = f"{district} {ptype}"

        projects.append({
            "project_id": project_id,
            "name": name,
            "type": ptype,
            "state": "Uttar Pradesh",
            "corridor_width_m": 0,
            "land_required_ha": round(sample_size * 0.4, 2),
            "target_days": int(np.random.choice([180, 270, 365, 540, 730])),
            "total_parcels": sample_size,
            "data_source": "synthetic"
        })

        for pid in sampled["parcel_id"].tolist():
            project_parcel_links.append({
                "project_id": project_id,
                "parcel_id": pid
            })

        print(f"  {project_id}: {name} — {sample_size} parcels (district-based)")

# Save
pd.DataFrame(projects).to_csv(f"{BASE_SYNTHETIC}/projects.csv", index=False)
pd.DataFrame(project_parcel_links).to_csv(f"{BASE_SYNTHETIC}/project_parcel_links.csv", index=False)

print(f"\n✅ Generated {len(projects)} projects")
print(f"   Total parcel-project links: {len(project_parcel_links)}")

print("\n" + "=" * 70)
print("✅ SCRIPT 4 COMPLETE!")
print("=" * 70)

"""
BHOOMISETU - Script 3: Generate Synthetic Parcels
Creates ~5,000 parcels inside sampled real village boundaries.
Samples ~100-150 villages to keep generation fast.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import geopandas as gpd
import numpy as np
from shapely.geometry import box
import uuid
from pathlib import Path
import json

BASE_PROCESSED = "D:/data/processed"
BASE_SYNTHETIC = "D:/data/synthetic"

Path(BASE_SYNTHETIC).mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("BHOOMISETU - Script 3: Generate Synthetic Parcels")
print("=" * 70)

# Load villages
village_path = f"{BASE_PROCESSED}/villages.geojson"
villages = gpd.read_file(village_path)
print(f"✅ Loaded {len(villages)} villages total")

# ============================================================================
# SAMPLE VILLAGES (~100-150 to target ~5,000 parcels)
# ============================================================================
TARGET_TOTAL = 5000
SAMPLE_SIZE = min(150, len(villages))
PARCELS_PER_VILLAGE = TARGET_TOTAL // SAMPLE_SIZE  # ~33-50 per village

np.random.seed(42)

# Prefer larger villages (more area = more realistic parcels)
villages['_area'] = villages.geometry.area
villages_sorted = villages.sort_values('_area', ascending=False)

# Sample with area-weighted probability
areas = villages['_area'].values
areas_positive = np.maximum(areas, 1e-10)
probs = areas_positive / areas_positive.sum()
sample_indices = np.random.choice(len(villages), size=SAMPLE_SIZE, replace=False, p=probs)
sampled_villages = villages.iloc[sample_indices].copy()

print(f"✅ Sampled {len(sampled_villages)} villages for parcel generation")

# ============================================================================
# PARCEL GENERATION
# ============================================================================
def subdivide_into_parcels(polygon, target_count=50):
    """Grid-subdivide a polygon into parcels."""
    if polygon is None or polygon.is_empty:
        return []

    # Handle MultiPolygon
    if polygon.geom_type == "MultiPolygon":
        all_cells = []
        for p in polygon.geoms:
            all_cells.extend(subdivide_into_parcels(p, target_count // max(1, len(list(polygon.geoms)))))
        return all_cells

    if polygon.geom_type != "Polygon":
        return []

    minx, miny, maxx, maxy = polygon.bounds
    area = polygon.area

    if area <= 0:
        return []

    # Estimate grid size
    cell_side = max(0.0001, np.sqrt(area / max(1, target_count)))
    xs = np.arange(minx, maxx, cell_side)
    ys = np.arange(miny, maxy, cell_side)

    cells = []
    for x in xs:
        for y in ys:
            cell = box(x, y, x + cell_side, y + cell_side)
            try:
                clipped = cell.intersection(polygon)
            except Exception:
                continue
            if not clipped.is_empty and clipped.area > 0:
                if clipped.geom_type == "Polygon":
                    cells.append(clipped)
                elif clipped.geom_type == "MultiPolygon":
                    for part in clipped.geoms:
                        if part.area > 0:
                            cells.append(part)
    return cells

# Find column names
cols = sampled_villages.columns.tolist()
state_col = next((c for c in cols if 'state' in c.lower() or 'st_nm' in c.lower()), None)
district_col = next((c for c in cols if 'district' in c.lower() or 'dist' in c.lower()), None)
village_col = next((c for c in cols if 'village' in c.lower() or 'vlg' in c.lower() or 'name' in c.lower()), None)

# Fallback: use first string columns
str_cols = [c for c in cols if c != 'geometry' and c != '_area' and sampled_villages[c].dtype == 'object']
if not state_col and len(str_cols) > 0:
    state_col = str_cols[0]
if not district_col and len(str_cols) > 1:
    district_col = str_cols[1]
if not village_col and len(str_cols) > 2:
    village_col = str_cols[2]

print(f"\nUsing columns: State='{state_col}', District='{district_col}', Village='{village_col}'")

all_parcels = []
processed = 0

for idx, village in sampled_villages.iterrows():
    parcels = subdivide_into_parcels(village.geometry, target_count=PARCELS_PER_VILLAGE)

    for i, geom in enumerate(parcels):
        survey_num = f"{np.random.randint(1, 999)}/{np.random.randint(1, 999)}"
        all_parcels.append({
            "parcel_id": f"PCL-{uuid.uuid4().hex[:8].upper()}",
            "state": str(village.get(state_col, "Uttar Pradesh")) if state_col else "Uttar Pradesh",
            "district": str(village.get(district_col, "Unknown")) if district_col else "Unknown",
            "village": str(village.get(village_col, "Unknown")) if village_col else "Unknown",
            "survey_number": survey_num,
            "area_hectare": round(geom.area * 1.1e4, 3),
            "geometry": geom,
            "data_source": "synthetic"
        })

    processed += 1
    if processed % 25 == 0:
        print(f"  Processed {processed}/{len(sampled_villages)} villages, {len(all_parcels)} parcels so far...")

# Create GeoDataFrame
parcels_gdf = gpd.GeoDataFrame(all_parcels, crs=sampled_villages.crs)
parcels_gdf = parcels_gdf[parcels_gdf["area_hectare"] > 0.01]

# Cap at TARGET_TOTAL if we overshot
if len(parcels_gdf) > TARGET_TOTAL:
    parcels_gdf = parcels_gdf.sample(n=TARGET_TOTAL, random_state=42).reset_index(drop=True)
    print(f"  Capped to {TARGET_TOTAL} parcels")

# Save
output_path = f"{BASE_SYNTHETIC}/parcels_geometry.geojson"
parcels_gdf.to_file(output_path, driver="GeoJSON")

print(f"\n✅ Generated {len(parcels_gdf)} parcels")
print(f"   Saved to: {output_path}")
print(f"   Average area: {parcels_gdf['area_hectare'].mean():.2f} ha")
print(f"   Min area: {parcels_gdf['area_hectare'].min():.4f} ha")
print(f"   Max area: {parcels_gdf['area_hectare'].max():.2f} ha")

# Summary stats
summary = {
    "total_parcels": len(parcels_gdf),
    "sampled_villages": len(sampled_villages),
    "total_villages_available": len(villages),
    "avg_parcels_per_village": round(len(parcels_gdf) / len(sampled_villages), 1),
    "min_area_ha": float(parcels_gdf['area_hectare'].min()),
    "max_area_ha": float(parcels_gdf['area_hectare'].max()),
    "mean_area_ha": float(parcels_gdf['area_hectare'].mean())
}

with open(f"{BASE_SYNTHETIC}/parcels_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("\n" + "=" * 70)
print("✅ SCRIPT 3 COMPLETE!")
print("=" * 70)

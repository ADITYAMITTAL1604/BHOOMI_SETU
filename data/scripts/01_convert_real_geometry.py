"""
BHOOMISETU - Script 1: Convert Real Geometry
Converts your existing shapefiles to GeoJSON format.
IMPORTANT: Reprojects from LCC_WGS84 (Indian Lambert Conformal Conic) to WGS84 (EPSG:4326).
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import geopandas as gpd
import os
import json
from pyproj import CRS
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================
BASE_REAL = "D:/data/real"
BASE_PROCESSED = "D:/data/processed"
BASE_SYNTHETIC = "D:/data/synthetic"
BASE_MODEL = "D:/data/model"

# The actual CRS used by the shapefiles (from .prj file)
LCC_WKT = '''PROJCS["LCC_WGS84",
    GEOGCS["GCS_WGS_1984",
        DATUM["D_WGS_1984",
            SPHEROID["WGS_1984",6378137.0,298.257223563]],
        PRIMEM["Greenwich",0.0],
        UNIT["Degree",0.0174532925199433]],
    PROJECTION["Lambert_Conformal_Conic_2SP"],
    PARAMETER["False_Easting",4000000.0],
    PARAMETER["False_Northing",4000000.0],
    PARAMETER["Central_Meridian",80.0],
    PARAMETER["Standard_Parallel_1",12.472944],
    PARAMETER["Standard_Parallel_2",35.172806],
    PARAMETER["Latitude_Of_Origin",24.0],
    UNIT["Meter",1.0]]'''

LCC_CRS = CRS.from_wkt(LCC_WKT)
TARGET_CRS = CRS.from_epsg(4326)  # WGS84

# Create directories
for path in [BASE_PROCESSED, BASE_SYNTHETIC, BASE_MODEL]:
    Path(path).mkdir(parents=True, exist_ok=True)

def load_and_reproject(filepath, name):
    """Load shapefile and reproject from LCC to WGS84."""
    print(f"  Loading {name}...")
    gdf = gpd.read_file(filepath)
    print(f"  Loaded {len(gdf)} features (original CRS: {gdf.crs})")

    # Force the correct CRS (shapefiles report LCC but GeoJSON loses it)
    gdf = gdf.set_crs(LCC_CRS, allow_override=True)

    # Reproject to WGS84
    gdf_wgs84 = gdf.to_crs(TARGET_CRS)
    bounds = gdf_wgs84.total_bounds
    print(f"  Reprojected to WGS84: lon=[{bounds[0]:.2f}, {bounds[2]:.2f}], lat=[{bounds[1]:.2f}, {bounds[3]:.2f}]")
    return gdf_wgs84

print("=" * 70)
print("BHOOMISETU - Script 1: Real Geometry Conversion")
print("=" * 70)

# ============================================================================
# 1. LOAD STATE BOUNDARIES
# ============================================================================
print("\n[1/5] State Boundaries...")
state_path = f"{BASE_REAL}/admin/State_District_Subdistrict_PAN INDIA/State Boundary/State Boundary.shp"
states = load_and_reproject(state_path, "State Boundary")

states.to_file(f"{BASE_PROCESSED}/states.geojson", driver="GeoJSON")
print(f"  [OK] Saved {len(states)} states to states.geojson")

# ============================================================================
# 2. LOAD DISTRICT BOUNDARIES
# ============================================================================
print("\n[2/5] District Boundaries...")
district_path = f"{BASE_REAL}/admin/State_District_Subdistrict_PAN INDIA/District_Subdistrict_PAN INDIA/District Boundary.shp"
districts = load_and_reproject(district_path, "District Boundary")

print(f"  Columns: {districts.columns.tolist()[:10]}...")

# Find state column
state_col = None
for col in districts.columns:
    col_lower = col.lower()
    if 'state' in col_lower or 'st_nm' in col_lower or 'name_1' in col_lower:
        state_col = col
        break

if state_col:
    print(f"  Using state column: '{state_col}'")
    up_mask = districts[state_col].str.upper().str.contains('UTTAR PRADESH', na=False)
    if up_mask.sum() == 0:
        up_mask = districts[state_col].str.upper().str.contains('UTTAR', na=False)
    up_districts = districts[up_mask]
    print(f"  [OK] Found {len(up_districts)} districts in Uttar Pradesh")
else:
    print("  WARNING: Could not find state column. Using all districts.")
    up_districts = districts

up_districts.to_file(f"{BASE_PROCESSED}/districts.geojson", driver="GeoJSON")
print(f"  [OK] Saved to districts.geojson")

# ============================================================================
# 3. LOAD SUB-DISTRICT (TEHSIL) BOUNDARIES
# ============================================================================
print("\n[3/5] Sub-District Boundaries...")
sub_path = f"{BASE_REAL}/admin/State_District_Subdistrict_PAN INDIA/District_Subdistrict_PAN INDIA/Sub_district Boundary.shp"
subdistricts = load_and_reproject(sub_path, "Sub_district Boundary")

if state_col and state_col in subdistricts.columns:
    up_mask = subdistricts[state_col].str.upper().str.contains('UTTAR PRADESH', na=False)
    if up_mask.sum() == 0:
        up_mask = subdistricts[state_col].str.upper().str.contains('UTTAR', na=False)
    up_sub = subdistricts[up_mask]
    print(f"  [OK] Found {len(up_sub)} sub-districts in UP")
else:
    up_sub = subdistricts

up_sub.to_file(f"{BASE_PROCESSED}/subdistricts.geojson", driver="GeoJSON")
print(f"  [OK] Saved to subdistricts.geojson")

# ============================================================================
# 4. LOAD VILLAGE BOUNDARIES (Already UP only)
# ============================================================================
print("\n[4/5] Village Boundaries...")
village_path = f"{BASE_REAL}/villages/UTTAR_PRADESH.shp"
villages = load_and_reproject(village_path, "UTTAR_PRADESH villages")

villages.to_file(f"{BASE_PROCESSED}/villages.geojson", driver="GeoJSON")
print(f"  [OK] Saved {len(villages)} villages to villages.geojson")

# ============================================================================
# 5. CREATE DATA SOURCE METADATA
# ============================================================================
print("\n[5/5] Creating data source metadata...")
metadata = {
    "original_crs": "LCC_WGS84 (Lambert Conformal Conic, false_easting=4000000, central_meridian=80)",
    "output_crs": "EPSG:4326 (WGS84)",
    "data_sources": {
        "states": {
            "source": "Real - Government Shapefile",
            "path": f"{BASE_PROCESSED}/states.geojson",
            "records": len(states)
        },
        "districts": {
            "source": "Real - Government Shapefile (filtered to UP)",
            "path": f"{BASE_PROCESSED}/districts.geojson",
            "records": len(up_districts)
        },
        "subdistricts": {
            "source": "Real - Government Shapefile (filtered to UP)",
            "path": f"{BASE_PROCESSED}/subdistricts.geojson",
            "records": len(up_sub)
        },
        "villages": {
            "source": "Real - Survey of India Shapefile",
            "path": f"{BASE_PROCESSED}/villages.geojson",
            "records": len(villages)
        }
    },
    "state_column_detected": state_col
}

with open(f"{BASE_PROCESSED}/metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print("  [OK] Metadata saved")

# Verify a sample coordinate
sample_bounds = up_districts.total_bounds
print(f"\n  Verification: UP district bounds (WGS84):")
print(f"    Longitude: {sample_bounds[0]:.4f} to {sample_bounds[2]:.4f}")
print(f"    Latitude:  {sample_bounds[1]:.4f} to {sample_bounds[3]:.4f}")

expected_lon = (77.0, 84.7)
expected_lat = (23.5, 30.5)
if expected_lon[0] < sample_bounds[0] < expected_lon[1] and expected_lat[0] < sample_bounds[1] < expected_lat[1]:
    print("  [OK] Coordinates look correct for Uttar Pradesh!")
else:
    print("  WARNING: Coordinates may not be correct. Please verify.")

print("\n" + "=" * 70)
print("[OK] SCRIPT 1 COMPLETE!")
print("=" * 70)
print(f"Processed files saved to: {BASE_PROCESSED}")

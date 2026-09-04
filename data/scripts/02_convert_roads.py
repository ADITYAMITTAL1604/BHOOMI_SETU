"""
BHOOMISETU - Script 2: Convert Roads
Extracts major roads from OSM PBF file using pyosmium.
Filters to UP bounding box and major highway types.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, box
from pathlib import Path

BASE_REAL = "D:/data/real"
BASE_PROCESSED = "D:/data/processed"

print("=" * 70)
print("BHOOMISETU - Script 2: Road Network Conversion")
print("=" * 70)

pbf_path = f"{BASE_REAL}/roads/india-260903.osm.pbf"

if not os.path.exists(pbf_path):
    print(f"ERROR: PBF file not found at {pbf_path}")
    sys.exit(1)

print(f"\n[OK] PBF file found: {pbf_path}")
print(f"     Size: {os.path.getsize(pbf_path) / (1024**3):.2f} GB")

# ============================================================================
# GET UP BOUNDING BOX FROM PROCESSED DISTRICTS
# ============================================================================
print("\n[1/4] Loading UP bounding box from districts...")
districts = gpd.read_file(f"{BASE_PROCESSED}/districts.geojson")
up_bounds = districts.total_bounds  # (minx, miny, maxx, maxy)
# Verify this is actual WGS84 (lon/lat should be small numbers, not millions)
if up_bounds[0] > 1000:
    print(f"     WARNING: Bounds {up_bounds} look like projected coords, not WGS84!")
    print("     Using hardcoded UP WGS84 bbox instead.")
    UP_BBOX = (76.9, 23.4, 84.7, 30.6)
else:
    # Add small buffer (in degrees)
    UP_BBOX = (up_bounds[0] - 0.1, up_bounds[1] - 0.1, up_bounds[2] + 0.1, up_bounds[3] + 0.1)
up_polygon = box(*UP_BBOX)
print(f"     UP bbox (WGS84): lon=[{UP_BBOX[0]:.2f}, {UP_BBOX[2]:.2f}], lat=[{UP_BBOX[1]:.2f}, {UP_BBOX[3]:.2f}]")

# ============================================================================
# MAJOR HIGHWAY TYPES TO EXTRACT
# ============================================================================
MAJOR_HIGHWAYS = {'motorway', 'trunk', 'primary', 'secondary',
                  'motorway_link', 'trunk_link', 'primary_link', 'secondary_link'}

# ============================================================================
# PYOSMIUM EXTRACTION
# ============================================================================
print("\n[2/4] Extracting roads from PBF with pyosmium...")
print("       Filtering to major roads within UP bounding box...")
print("       This may take 2-5 minutes for 1.66 GB file...")

import osmium

class RoadExtractor(osmium.SimpleHandler):
    """Extracts major road ways from PBF file with geometry reconstruction."""
    def __init__(self, bbox, highway_types):
        super().__init__()
        self.bbox = bbox  # (minx, miny, maxx, maxy)
        self.highway_types = highway_types
        self.roads = []
        self.total_ways = 0
        self.matched_ways = 0

    def way(self, w):
        self.total_ways += 1

        # Check highway tag
        highway = w.tags.get('highway')
        if highway not in self.highway_types:
            return

        # Build coordinate list from node locations
        try:
            coords = [(n.lon, n.lat) for n in w.nodes if n.location.valid()]
        except Exception:
            return

        if len(coords) < 2:
            return

        # Check if any point is within UP bbox
        minx, miny, maxx, maxy = self.bbox
        in_bbox = any(minx <= lon <= maxx and miny <= lat <= maxy
                      for lon, lat in coords)
        if not in_bbox:
            return

        self.matched_ways += 1

        # Extract attributes
        name = w.tags.get('name', '')
        ref = w.tags.get('ref', '')
        lanes = w.tags.get('lanes', '')
        surface = w.tags.get('surface', '')
        maxspeed = w.tags.get('maxspeed', '')

        self.roads.append({
            'osm_id': w.id,
            'highway': highway,
            'name': name,
            'ref': ref,
            'lanes': lanes,
            'surface': surface,
            'maxspeed': maxspeed,
            'coords': coords
        })

        if self.matched_ways % 1000 == 0:
            print(f"       ... {self.matched_ways} UP roads found (scanned {self.total_ways} ways)")

# Run extraction
extractor = RoadExtractor(UP_BBOX, MAJOR_HIGHWAYS)
try:
    extractor.apply_file(pbf_path, locations=True)
    print(f"\n     [OK] Scanned {extractor.total_ways} total ways")
    print(f"     [OK] Found {extractor.matched_ways} major roads in UP region")
except Exception as e:
    print(f"\n     ERROR: pyosmium extraction failed: {e}")
    print("     Trying without locations (node-level coords)...")

    # Fallback: use WKBFactory for geometry
    try:
        class RoadExtractorWKB(osmium.SimpleHandler):
            def __init__(self, highway_types):
                super().__init__()
                self.wkbfab = osmium.geom.WKBFactory()
                self.highway_types = highway_types
                self.roads = []
                self.total_ways = 0

            def way(self, w):
                self.total_ways += 1
                highway = w.tags.get('highway')
                if highway not in self.highway_types:
                    return
                try:
                    wkb = self.wkbfab.create_linestring(w)
                    from shapely import wkb as shapely_wkb
                    geom = shapely_wkb.loads(wkb, hex=True)
                    coords = list(geom.coords)
                except Exception:
                    return

                self.roads.append({
                    'osm_id': w.id,
                    'highway': highway,
                    'name': w.tags.get('name', ''),
                    'ref': w.tags.get('ref', ''),
                    'lanes': w.tags.get('lanes', ''),
                    'surface': w.tags.get('surface', ''),
                    'maxspeed': w.tags.get('maxspeed', ''),
                    'coords': coords
                })

                if len(self.roads) % 1000 == 0:
                    print(f"       ... {len(self.roads)} roads extracted")

        extractor = RoadExtractorWKB(MAJOR_HIGHWAYS)
        extractor.apply_file(pbf_path, locations=True)
        print(f"     [OK] Extracted {len(extractor.roads)} roads (WKB method)")
    except Exception as e2:
        print(f"     ERROR: WKB method also failed: {e2}")
        sys.exit(1)

if len(extractor.roads) == 0:
    print("     ERROR: No roads extracted!")
    sys.exit(1)

# ============================================================================
# BUILD GEODATAFRAME
# ============================================================================
print("\n[3/4] Building GeoDataFrame...")

geometries = []
attributes = []

for road in extractor.roads:
    try:
        line = LineString(road['coords'])
        if line.is_valid and not line.is_empty:
            geometries.append(line)
            attributes.append({
                'osm_id': road['osm_id'],
                'highway': road['highway'],
                'name': road['name'],
                'ref': road['ref'],
                'lanes': road['lanes'],
                'surface': road['surface'],
                'maxspeed': road['maxspeed']
            })
    except Exception:
        continue

roads_gdf = gpd.GeoDataFrame(attributes, geometry=geometries, crs="EPSG:4326")
print(f"     [OK] Built GeoDataFrame with {len(roads_gdf)} roads")

# Clip to UP boundary precisely
print("     Clipping to UP district boundaries...")
up_boundary = districts.dissolve().geometry.iloc[0]
roads_gdf = roads_gdf[roads_gdf.geometry.intersects(up_boundary)]
print(f"     [OK] {len(roads_gdf)} roads within UP boundaries")

# ============================================================================
# SAVE
# ============================================================================
print("\n[4/4] Saving to GeoJSON...")
output_path = f"{BASE_PROCESSED}/roads.geojson"
roads_gdf.to_file(output_path, driver="GeoJSON")

# Summary
print(f"\n     [OK] Saved to {output_path}")
print(f"\n     Road type breakdown:")
for htype, count in roads_gdf['highway'].value_counts().items():
    print(f"       {htype:20s}: {count}")

# Save metadata
road_meta = {
    "source": "Real - OpenStreetMap PBF",
    "pbf_file": pbf_path,
    "total_roads": len(roads_gdf),
    "highway_types": roads_gdf['highway'].value_counts().to_dict(),
    "bounding_box": list(UP_BBOX),
    "crs": "EPSG:4326"
}
with open(f"{BASE_PROCESSED}/roads_metadata.json", "w") as f:
    json.dump(road_meta, f, indent=2)

print("\n" + "=" * 70)
print("[OK] SCRIPT 2 COMPLETE — REAL ROAD DATA!")
print("=" * 70)

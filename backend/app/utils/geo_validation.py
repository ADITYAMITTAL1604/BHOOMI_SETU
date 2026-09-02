"""Geospatial validation and sanitization utilities for BhoomiSetu.

Enforces:
- Malformed GeoJSON/WKT detection
- Self-intersecting polygon rejection
- Vertex count limits (≤ 50,000 vertices)
- India geographical bounding box constraint
- Viewport bounding box dimension limits
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple, Union

from fastapi import HTTPException, status
import shapely
import shapely.wkt
import shapely.geometry
import shapely.validation

# India Mainland & Islands Bounding Box (with slight buffer for maritime EEZ / territorial waters)
# Southernmost: Indira Point ~6.7° N -> 6.0° N
# Northernmost: Siachen / Indira Col ~37.1° N -> 38.5° N
# Westernmost: Ghuar Mota, Gujarat ~68.1° E -> 68.0° E
# Easternmost: Kibithu, Arunachal Pradesh ~97.4° E -> 98.0° E
INDIA_MIN_LON = 68.0
INDIA_MAX_LON = 98.0
INDIA_MIN_LAT = 6.0
INDIA_MAX_LAT = 38.5

MAX_GEOMETRY_VERTICES = 50_000
MAX_VIEWPORT_SPAN_DEGREES = 15.0


def validate_viewport_bbox(
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
) -> None:
    """Validate viewport bounding box for parcel spatial queries.

    Rejects:
    - Inverted coordinates (min >= max)
    - Coordinates outside India
    - Overly broad viewport bounding boxes covering the entire country (> 15° span)
    """
    if min_lon >= max_lon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bounding box: min_lon must be strictly less than max_lon.",
        )
    if min_lat >= max_lat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid bounding box: min_lat must be strictly less than max_lat.",
        )

    # Check India bounds
    if (
        min_lon < INDIA_MIN_LON
        or max_lon > INDIA_MAX_LON
        or min_lat < INDIA_MIN_LAT
        or max_lat > INDIA_MAX_LAT
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Bounding box coordinates [{min_lon}, {min_lat}, {max_lon}, {max_lat}] fall outside "
                f"India's territory (Lon: {INDIA_MIN_LON}°-{INDIA_MAX_LON}°, Lat: {INDIA_MIN_LAT}°-{INDIA_MAX_LAT}°)."
            ),
        )

    # Check span: reject overly broad queries covering all of India
    lon_span = max_lon - min_lon
    lat_span = max_lat - min_lat
    if lon_span >= MAX_VIEWPORT_SPAN_DEGREES or lat_span >= MAX_VIEWPORT_SPAN_DEGREES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Viewport bounding box is too broad ({lon_span:.1f}° x {lat_span:.1f}°). "
                f"Maximum allowable viewport span is {MAX_VIEWPORT_SPAN_DEGREES}° to prevent overload. "
                "Please zoom into a specific district or project corridor."
            ),
        )


def validate_and_parse_geometry(geom_input: Union[str, Dict[str, Any]]) -> shapely.Geometry:
    """Parse and validate WKT or GeoJSON geometry object.

    Checks:
    1. Malformed syntax
    2. Self-intersection and topological validity
    3. Vertex count limit (≤ 50,000)
    4. India geographical bounding box constraint

    Returns
    -------
    shapely.Geometry: validated geometry object

    Raises
    ------
    HTTPException 400: on any validation failure
    """
    if not geom_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geometry data cannot be empty.",
        )

    # 1. Parse WKT or GeoJSON
    try:
        if isinstance(geom_input, dict):
            geom = shapely.geometry.shape(geom_input)
        elif isinstance(geom_input, str):
            s = geom_input.strip()
            if s.startswith("{"):
                # GeoJSON string
                d = json.loads(s)
                geom = shapely.geometry.shape(d)
            else:
                # WKT string
                geom = shapely.wkt.loads(s)
        else:
            raise ValueError(f"Unsupported geometry type: {type(geom_input)}")
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed GeoJSON string: {str(exc)}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed geometry: unable to parse ({str(exc)})",
        )

    if geom.is_empty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geometry is empty.",
        )

    # 2. Check topological validity (e.g. self-intersecting polygons)
    if not geom.is_valid:
        # Get explanation why it is invalid
        explanation = shapely.validation.explain_validity(geom)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Topologically invalid geometry: {explanation}",
        )

    # 3. Check vertex count
    num_coords = shapely.get_num_coordinates(geom)
    if num_coords > MAX_GEOMETRY_VERTICES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Geometry vertex count ({num_coords:,}) exceeds the maximum allowed limit "
                f"of {MAX_GEOMETRY_VERTICES:,} vertices. Please simplify the geometry before uploading."
            ),
        )

    # 4. Check coordinates within India bounding box
    minx, miny, maxx, maxy = geom.bounds
    if (
        minx < INDIA_MIN_LON
        or maxx > INDIA_MAX_LON
        or miny < INDIA_MIN_LAT
        or maxy > INDIA_MAX_LAT
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Geometry coordinates [{minx:.3f}, {miny:.3f}, {maxx:.3f}, {maxy:.3f}] fall outside "
                f"India's territory (Lon: {INDIA_MIN_LON}°-{INDIA_MAX_LON}°, Lat: {INDIA_MIN_LAT}°-{INDIA_MAX_LAT}°)."
            ),
        )

    return geom

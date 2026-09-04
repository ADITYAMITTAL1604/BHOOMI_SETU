"""FastAPI router for /gis endpoints (spatial queries, GeoJSON)."""

import json
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from geoalchemy2.functions import (
    ST_AsGeoJSON,
    ST_Within,
    ST_MakeEnvelope,
    ST_IsValid,
)

from app.core.deps import get_current_user
from app.database import get_db
from app.models import Parcel, Project, GISBoundary

router = APIRouter()


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class BoundingBox(BaseModel):
    """Viewport bounding box for parcel spatial query."""
    min_lon: float = Field(..., description="West longitude")
    min_lat: float = Field(..., description="South latitude")
    max_lon: float = Field(..., description="East longitude")
    max_lat: float = Field(..., description="North latitude")

    @validator("max_lat")
    def validate_bbox_coordinates(cls, v, values):
        if "min_lon" in values and "min_lat" in values and "max_lon" in values:
            from app.utils.geo_validation import validate_viewport_bbox
            validate_viewport_bbox(values["min_lon"], values["min_lat"], values["max_lon"], v)
        return v

    def validate_bbox(self):
        from app.utils.geo_validation import validate_viewport_bbox
        validate_viewport_bbox(self.min_lon, self.min_lat, self.max_lon, self.max_lat)


VALID_BOUNDARY_LEVELS = {"state", "district", "village"}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _safe_geojson(db: Session, geometry_col) -> Optional[dict]:
    """Convert geometry column to GeoJSON dict across PostgreSQL (PostGIS) and SQLite."""
    if geometry_col is None:
        return None

    # 1. If stored as WKT string (e.g. SQLite storage)
    if isinstance(geometry_col, str):
        try:
            import shapely.wkt
            import shapely.geometry
            shape = shapely.wkt.loads(geometry_col)
            return shapely.geometry.mapping(shape)
        except Exception:
            pass

    # 2. Try PostGIS ST_AsGeoJSON
    try:
        raw = db.execute(select(ST_AsGeoJSON(geometry_col))).scalar()
        if raw:
            return json.loads(raw)
    except Exception:
        pass

    # 3. Try GeoAlchemy2 to_shape
    try:
        from geoalchemy2.shape import to_shape
        import shapely.geometry
        shape = to_shape(geometry_col)
        return shapely.geometry.mapping(shape)
    except Exception:
        pass

    return None


def _build_feature(geometry_geojson: Optional[dict], properties: dict) -> dict:
    """Build a GeoJSON Feature dict."""
    return {
        "type": "Feature",
        "geometry": geometry_geojson,
        "properties": properties,
    }


def _feature_collection(features: list[dict]) -> dict:
    """Wrap a list of Feature dicts in a FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": features,
        "count": len(features),
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.get(
    "/boundaries/{level}",
    summary="Serve administrative boundary GeoJSON",
    response_model=dict,
)
def get_boundaries(
    level: str,
    state: Optional[str] = Query(None, description="Filter by state name"),
    district: Optional[str] = Query(None, description="Filter by district name (for village level)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """
    Return a GeoJSON FeatureCollection of administrative boundaries.

    - **level**: `state` | `district` | `village`
    - Optionally filter by `state` or `district` name.
    """
    if level not in VALID_BOUNDARY_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid level '{level}'. Must be one of: {sorted(VALID_BOUNDARY_LEVELS)}",
        )

    stmt = select(GISBoundary).where(GISBoundary.level == level)

    if state:
        stmt = stmt.where(GISBoundary.state_name.ilike(f"%{state}%"))
    if district and level == "village":
        stmt = stmt.where(GISBoundary.district_name.ilike(f"%{district}%"))

    stmt = stmt.order_by(GISBoundary.name)
    boundaries = db.execute(stmt).scalars().all()

    features = []
    for boundary in boundaries:
        geojson = _safe_geojson(db, boundary.geometry)
        features.append(_build_feature(
            geojson,
            {
                "boundary_id": str(boundary.boundary_id),
                "level": boundary.level,
                "name": boundary.name,
                "parent_name": boundary.parent_name,
                "state_name": boundary.state_name,
                "district_name": boundary.district_name,
            },
        ))

    return _feature_collection(features)


@router.get(
    "/projects/{project_id}/geojson",
    summary="Serve a project's parcels as GeoJSON FeatureCollection",
    response_model=dict,
)
def get_project_geojson(
    project_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """
    Return all parcels for a project as a GeoJSON FeatureCollection.
    If project_id is 'all', returns parcels across all projects (scoped to user).
    """
    from app.core.deps import get_user_geographic_scope
    scope = get_user_geographic_scope(current_user)

    if project_id in ("all", "ALL"):
        stmt = select(Parcel).where(Parcel.geometry.isnot(None))
        if scope.get("state"):
            stmt = stmt.where(Parcel.state == scope["state"])
        if scope.get("district"):
            stmt = stmt.where(Parcel.district == scope["district"])
        parcels = db.execute(stmt.limit(1000)).scalars().all()

        features = []
        for parcel in parcels:
            geojson = _safe_geojson(db, parcel.geometry)
            if geojson:
                features.append(_build_feature(
                    geojson,
                    {
                        "parcel_id": str(parcel.parcel_id),
                        "project_id": str(parcel.project_id),
                        "survey_number": parcel.survey_number,
                        "area_ha": parcel.area_ha,
                        "owner_name": parcel.owner_name,
                        "owner_reference": parcel.owner_reference,
                        "current_stage": parcel.current_stage,
                        "status": parcel.status,
                        "risk_score": parcel.risk_score,
                        "village": parcel.village,
                        "district": parcel.district,
                        "state": parcel.state,
                    },
                ))

        return {
            **_feature_collection(features),
            "project_id": "all",
            "project_name": "All Projects (Portfolio View)",
        }

    # Resolve specific project
    project = None
    if project_id == "default":
        proj_stmt = select(Project)
        if scope.get("state"):
            proj_stmt = proj_stmt.where(Project.states.any(scope["state"]))
        if scope.get("district"):
            proj_stmt = proj_stmt.where(Project.districts.any(scope["district"]))
        project = db.execute(proj_stmt.order_by(Project.created_at.desc())).scalars().first()
    else:
        try:
            pid = UUID(project_id)
            project = db.execute(select(Project).where(Project.project_id == pid)).scalar_one_or_none()
        except (ValueError, TypeError):
            project = db.execute(select(Project).order_by(Project.created_at.desc())).scalars().first()

    if not project:
        return _feature_collection([])

    parcels = db.execute(
        select(Parcel).where(Parcel.project_id == project.project_id)
    ).scalars().all()

    features = []
    for parcel in parcels:
        geojson = _safe_geojson(db, parcel.geometry)
        if geojson:
            features.append(_build_feature(
                geojson,
                {
                    "parcel_id": str(parcel.parcel_id),
                    "project_id": str(parcel.project_id),
                    "survey_number": parcel.survey_number,
                    "area_ha": parcel.area_ha,
                    "owner_name": parcel.owner_name,
                    "owner_reference": parcel.owner_reference,
                    "current_stage": parcel.current_stage,
                    "status": parcel.status,
                    "risk_score": parcel.risk_score,
                    "village": parcel.village,
                    "district": parcel.district,
                    "state": parcel.state,
                },
            ))

    return {
        **_feature_collection(features),
        "project_id": str(project.project_id),
        "project_name": project.name,
    }


@router.post(
    "/parcels/within",
    summary="Viewport bounding-box parcel query (≤ 500 results)",
    response_model=dict,
)
def parcels_within_bbox(
    bbox: BoundingBox,
    project_id: Optional[UUID] = Query(None, description="Optionally filter by project"),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """
    Return parcels whose geometry falls within the given bounding box.

    - Results are capped at **500** features.
    - Geometries without a PostGIS polygon are included as `null` geometry features.
    """
    bbox.validate_bbox()

    # Build the envelope
    envelope = ST_MakeEnvelope(
        bbox.min_lon, bbox.min_lat,
        bbox.max_lon, bbox.max_lat,
        4326,
    )

    # Select parcels with non-null geometries within the bbox
    stmt = (
        select(Parcel)
        .where(Parcel.geometry.isnot(None))
        .where(ST_Within(Parcel.geometry, envelope))
    )

    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)

    if status_filter:
        stmt = stmt.where(Parcel.status == status_filter)

    # Cap at 500
    stmt = stmt.limit(500)

    parcels = db.execute(stmt).scalars().all()

    features = []
    for parcel in parcels:
        geojson = None
        if parcel.geometry is not None:
            try:
                raw = db.execute(
                    select(ST_AsGeoJSON(parcel.geometry))
                ).scalar()
                geojson = json.loads(raw) if raw else None
            except Exception:
                geojson = None

        features.append(_build_feature(
            geojson,
            {
                "parcel_id": str(parcel.parcel_id),
                "project_id": str(parcel.project_id),
                "survey_number": parcel.survey_number,
                "area_ha": parcel.area_ha,
                "owner_name": parcel.owner_name,
                "current_stage": parcel.current_stage,
                "status": parcel.status,
                "risk_score": parcel.risk_score,
                "village": parcel.village,
                "district": parcel.district,
                "state": parcel.state,
            },
        ))

    return {
        **_feature_collection(features),
        "capped": len(features) == 500,
        "bbox": {
            "min_lon": bbox.min_lon,
            "min_lat": bbox.min_lat,
            "max_lon": bbox.max_lon,
            "max_lat": bbox.max_lat,
        },
    }

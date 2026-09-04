"""FastAPI router for Parcel CRUD operations."""

from typing import Optional, List
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.orm import Session, selectinload
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_GeomFromText, ST_AsGeoJSON, ST_IsValid, ST_MakeValid

from app.core.deps import (
    get_current_user,
    get_user_geographic_scope,
    filter_by_geographic_scope,
    require_district_or_above,
    require_state_or_above,
)
from app.database import get_db
from app.models import Parcel, Project, AcquisitionStage, Compensation, RRRecord
from app.models.enums import ParcelStatus, StageName, StageStatus, UserRole
from app.services.transition import execute_transition
from app.utils.pagination import PageParams, PageResponse, paginate, create_page_response

router = APIRouter()


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class ParcelBase(BaseModel):
    project_id: UUID
    survey_number: str = Field(..., min_length=1, max_length=100)
    area_ha: float = Field(..., gt=0)
    geometry_wkt: Optional[str] = None
    owner_name: str = Field(default="")
    owner_reference: str = Field(default="")
    village: str = Field(default="")
    district: str = Field(default="")
    state: str = Field(default="")
    assigned_officer: Optional[UUID] = None

    @validator("survey_number", "owner_name", "owner_reference", "village", "district", "state", pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            from app.utils.sanitization import sanitize_text
            return sanitize_text(v)
        return v


class ParcelCreate(ParcelBase):
    @validator("geometry_wkt")
    def validate_geometry(cls, v):
        if v is not None and v.strip() == "":
            return None
        if v is not None and isinstance(v, str) and v.strip():
            from app.utils.geo_validation import validate_and_parse_geometry
            validate_and_parse_geometry(v)
        return v


PROTECTED_PARCEL_FIELDS = {"current_stage", "status", "risk_score"}


class ParcelUpdate(BaseModel):
    """Standard parcel update schema. Protected workflow/ML fields are excluded to prevent mass assignment."""
    survey_number: Optional[str] = Field(None, min_length=1, max_length=100)
    area_ha: Optional[float] = Field(None, gt=0)
    geometry_wkt: Optional[str] = None
    owner_name: Optional[str] = None
    owner_reference: Optional[str] = None
    village: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    assigned_officer: Optional[UUID] = None
    remarks: Optional[str] = None

    @validator("survey_number", "owner_name", "owner_reference", "village", "district", "state", "remarks", pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            from app.utils.sanitization import sanitize_text
            return sanitize_text(v)
        return v

    @validator("geometry_wkt")
    def validate_geometry(cls, v):
        if v is not None and v.strip() == "":
            return None
        if v is not None and isinstance(v, str) and v.strip():
            from app.utils.geo_validation import validate_and_parse_geometry
            validate_and_parse_geometry(v)
        return v


class ParcelAdminUpdate(ParcelUpdate):
    """Admin-only schema permitting direct overrides of workflow stage, status, and ML risk scores."""
    current_stage: Optional[StageName] = None
    status: Optional[ParcelStatus] = None
    risk_score: Optional[float] = Field(None, ge=0, le=100)


class ParcelResponse(BaseModel):
    parcel_id: UUID
    project_id: UUID
    survey_number: str
    area_ha: float
    geometry: Optional[dict] = None
    owner_name: str
    owner_reference: str
    current_stage: StageName
    status: ParcelStatus
    risk_score: float
    village: str
    district: str
    state: str
    assigned_officer: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    stages: List[dict] = []

    class Config:
        from_attributes = True


class ParcelListResponse(BaseModel):
    parcel_id: UUID
    project_id: UUID
    survey_number: str
    area_ha: float
    owner_name: str
    current_stage: StageName
    status: ParcelStatus
    risk_score: float
    village: str
    district: str
    state: str
    assigned_officer: Optional[UUID]

    class Config:
        from_attributes = True


class BulkParcelCreate(BaseModel):
    parcels: List[ParcelCreate]


class ParcelGeometryValidate(BaseModel):
    geometry_wkt: str = Field(..., min_length=1)


class ParcelTransitionRequest(BaseModel):
    target_stage: StageName
    status: Optional[ParcelStatus] = None
    remarks: Optional[str] = None
    sla_target_date: Optional[date] = None


# ─── Helpers ──────────────────────────────────────────────────────────────────

from datetime import datetime


def _apply_parcel_scope(stmt, user):
    """Apply geographic scope filtering for parcels."""
    scope = get_user_geographic_scope(user)
    conditions = []

    if scope.get("state"):
        conditions.append(Parcel.state == scope["state"])
    if scope.get("district"):
        conditions.append(Parcel.district == scope["district"])

    if conditions:
        stmt = stmt.where(and_(*conditions))
    return stmt


def _validate_and_clean_geometry(db: Session, wkt: str) -> Optional[str]:
    """Validate WKT geometry and return cleaned WKT or raise HTTPException."""
    if not wkt or not wkt.strip():
        return None

    try:
        # First check if it's valid
        result = db.execute(
            select(ST_IsValid(ST_GeomFromText(wkt, 4326)))
        ).scalar()

        if not result:
            # Try to make it valid
            result = db.execute(
                select(ST_AsGeoJSON(ST_MakeValid(ST_GeomFromText(wkt, 4326))))
            ).scalar()
            if result:
                import json
                geom = json.loads(result)
                return geom  # Return as GeoJSON dict for storage
            raise ValueError("Geometry is invalid and cannot be fixed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid geometry: {str(e)}",
        )

    return wkt


def _convert_geometry_to_geojson(db: Session, geometry_col) -> Optional[dict]:
    """Convert PostGIS geometry to GeoJSON dict."""
    if geometry_col is None:
        return None
    try:
        result = db.execute(select(ST_AsGeoJSON(geometry_col))).scalar()
        if result:
            import json
            return json.loads(result)
    except Exception:
        pass
    return None


def _build_stages_response(db: Session, parcel_id: UUID) -> List[dict]:
    """Build stages response for a parcel."""
    stages = db.execute(
        select(AcquisitionStage)
        .where(AcquisitionStage.parcel_id == parcel_id)
        .order_by(AcquisitionStage.stage_order)
    ).scalars().all()

    return [
        {
            "stage_id": str(s.stage_id),
            "stage_name": s.stage_name,
            "stage_order": s.stage_order,
            "start_date": s.start_date.isoformat() if s.start_date else None,
            "target_date": s.target_date.isoformat() if s.target_date else None,
            "completion_date": s.completion_date.isoformat() if s.completion_date else None,
            "status": s.status,
            "assigned_officer": str(s.assigned_officer) if s.assigned_officer else None,
            "remarks": s.remarks,
        }
        for s in stages
    ]


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=ParcelResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new parcel",
)
def create_parcel(
    parcel_data: ParcelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_district_or_above),
):
    """Create a new parcel with geometry validation. Requires DISTRICT role or above."""
    # Verify project exists and user has access
    project = db.execute(
        select(Project).where(Project.project_id == parcel_data.project_id)
    ).scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check geographic scope
    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and parcel_data.state != scope["state"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot create parcel in state '{parcel_data.state}' outside your scope",
        )
    if scope.get("district") and parcel_data.district != scope["district"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot create parcel in district '{parcel_data.district}' outside your scope",
        )

    # Validate geometry
    geometry = None
    if parcel_data.geometry_wkt:
        geometry = ST_GeomFromText(parcel_data.geometry_wkt, 4326)

    parcel = Parcel(
        project_id=parcel_data.project_id,
        survey_number=parcel_data.survey_number,
        area_ha=parcel_data.area_ha,
        geometry=geometry,
        owner_name=parcel_data.owner_name,
        owner_reference=parcel_data.owner_reference,
        village=parcel_data.village,
        district=parcel_data.district,
        state=parcel_data.state,
        assigned_officer=parcel_data.assigned_officer,
    )
    db.add(parcel)
    db.commit()
    db.refresh(parcel)

    return _build_parcel_response(db, parcel)


@router.post(
    "/bulk",
    response_model=List[ParcelResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple parcels",
)
def create_parcels_bulk(
    bulk_data: BulkParcelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_district_or_above),
):
    """Create multiple parcels in bulk. Requires DISTRICT role or above."""
    if not bulk_data.parcels or len(bulk_data.parcels) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 1 parcel is required in bulk create request.",
        )
    if len(bulk_data.parcels) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 500 parcels per bulk request",
        )

    # Group by project for validation
    project_ids = set(p.project_id for p in bulk_data.parcels)
    projects = db.execute(
        select(Project).where(Project.project_id.in_(project_ids))
    ).scalars().all()
    project_map = {p.project_id: p for p in projects}

    scope = get_user_geographic_scope(current_user)
    created_parcels = []

    for parcel_data in bulk_data.parcels:
        # Validate project
        if parcel_data.project_id not in project_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project {parcel_data.project_id} not found",
            )

        # Check scope
        if scope.get("state") and parcel_data.state != scope["state"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Parcel {parcel_data.survey_number}: state outside scope",
            )
        if scope.get("district") and parcel_data.district != scope["district"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Parcel {parcel_data.survey_number}: district outside scope",
            )

        geometry = None
        if parcel_data.geometry_wkt:
            geometry = ST_GeomFromText(parcel_data.geometry_wkt, 4326)

        parcel = Parcel(
            project_id=parcel_data.project_id,
            survey_number=parcel_data.survey_number,
            area_ha=parcel_data.area_ha,
            geometry=geometry,
            owner_name=parcel_data.owner_name,
            owner_reference=parcel_data.owner_reference,
            village=parcel_data.village,
            district=parcel_data.district,
            state=parcel_data.state,
            assigned_officer=parcel_data.assigned_officer,
        )
        db.add(parcel)
        created_parcels.append(parcel)

    db.commit()
    for p in created_parcels:
        db.refresh(p)

    return [_build_parcel_response(db, p) for p in created_parcels]


@router.get(
    "",
    response_model=PageResponse[ParcelListResponse],
    summary="List parcels with pagination and filters",
)
def list_parcels(
    page_params: PageParams = Depends(),
    project_id: Optional[UUID] = Query(None),
    search: Optional[str] = Query(None, description="Search in survey_number, owner_name"),
    q: Optional[str] = Query(None),
    status_filter: Optional[ParcelStatus] = Query(None, alias="status"),
    stage_filter: Optional[StageName] = Query(None, alias="stage"),
    district: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    assigned_officer: Optional[UUID] = Query(None),
    min_risk: Optional[float] = Query(None, ge=0),
    max_risk: Optional[float] = Query(None, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List parcels with pagination, search, and filters. Scope-enforced."""
    search_term_val = search or q
    stmt = select(Parcel)

    # Apply geographic scope
    stmt = _apply_parcel_scope(stmt, current_user)

    # Apply filters
    if project_id:
        stmt = stmt.where(Parcel.project_id == project_id)

    if search_term_val:
        search_term = f"%{search_term_val}%"
        stmt = stmt.where(
            or_(
                Parcel.survey_number.ilike(search_term),
                Parcel.owner_name.ilike(search_term),
            )
        )

    if status_filter:
        stmt = stmt.where(Parcel.status == status_filter)

    if stage_filter:
        stmt = stmt.where(Parcel.current_stage == stage_filter)

    if district:
        stmt = stmt.where(Parcel.district == district)

    if state:
        stmt = stmt.where(Parcel.state == state)

    if assigned_officer:
        stmt = stmt.where(Parcel.assigned_officer == assigned_officer)

    if min_risk is not None:
        stmt = stmt.where(Parcel.risk_score >= min_risk)

    if max_risk is not None:
        stmt = stmt.where(Parcel.risk_score <= max_risk)

    stmt = stmt.order_by(desc(Parcel.risk_score), Parcel.created_at.desc())

    items, total = paginate(stmt, page_params.page, page_params.page_size, db=db)

    response_items = [ParcelListResponse.model_validate(p) for p in items]
    return create_page_response(response_items, total, page_params.page, page_params.page_size)


@router.get(
    "/{parcel_id}",
    response_model=ParcelResponse,
    summary="Get parcel by ID",
)
def get_parcel(
    parcel_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single parcel by ID with stages. Scope-enforced."""
    parcel = db.execute(select(Parcel).where(Parcel.parcel_id == parcel_id)).scalar_one_or_none()
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found",
        )

    # 1. Geographic scope check (cross-district / cross-state access -> 403)
    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and parcel.state and parcel.state != scope["state"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: parcel is in state '{parcel.state}', outside your state scope '{scope['state']}'",
        )
    if scope.get("district") and parcel.district and parcel.district != scope["district"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: parcel is in district '{parcel.district}', outside your district scope '{scope['district']}'",
        )

    # 2. Field officer check (unassigned parcel access -> 403)
    user_role = getattr(current_user, "role", None)
    role_val = user_role.value if hasattr(user_role, "value") else str(user_role)
    if role_val in (UserRole.FIELD_OFFICER.value, "FIELD_OFFICER"):
        if parcel.assigned_officer != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: this parcel is not assigned to you",
            )

    return _build_parcel_response(db, parcel)


from typing import Union

@router.put(
    "/{parcel_id}",
    response_model=ParcelResponse,
    summary="Update parcel",
)
async def update_parcel(
    parcel_id: UUID,
    parcel_data: ParcelAdminUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_district_or_above),
):
    """Update a parcel. Requires DISTRICT role or above. Direct workflow/risk overrides require ADMIN."""
    # Enforce mass assignment protection on protected fields
    user_role = getattr(current_user, "role", None)
    role_val = user_role.value if hasattr(user_role, "value") else str(user_role)
    is_admin = role_val in (UserRole.ADMIN.value, "ADMIN")

    try:
        raw_body = await request.json()
    except Exception:
        raw_body = {}

    if not is_admin:
        for protected_field in PROTECTED_PARCEL_FIELDS:
            has_in_model = getattr(parcel_data, protected_field, None) is not None
            has_in_raw = isinstance(raw_body, dict) and protected_field in raw_body and raw_body[protected_field] is not None
            if has_in_model or has_in_raw:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: Modifying '{protected_field}' directly requires ADMIN privileges. "
                           f"Use the workflow transition service or ML re-scoring endpoint.",
                )

    parcel = db.execute(select(Parcel).where(Parcel.parcel_id == parcel_id)).scalar_one_or_none()
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found",
        )

    # Check existing parcel scope
    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and parcel.state and parcel.state != scope["state"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: cannot modify parcel in state '{parcel.state}' outside your scope",
        )
    if scope.get("district") and parcel.district and parcel.district != scope["district"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: cannot modify parcel in district '{parcel.district}' outside your scope",
        )

    # Check scope for state/district changes
    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and parcel_data.state and parcel_data.state != scope["state"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot move parcel to state outside your scope",
        )
    if scope.get("district") and parcel_data.district and parcel_data.district != scope["district"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Cannot move parcel to district outside your scope",
        )

    # Update fields
    update_data = parcel_data.model_dump(exclude_unset=True)
    geometry_wkt = update_data.pop("geometry_wkt", None)
    remarks = update_data.pop("remarks", None)

    if geometry_wkt is not None:
        if geometry_wkt:
            parcel.geometry = ST_GeomFromText(geometry_wkt, 4326)
        else:
            parcel.geometry = None

    old_status = parcel.status
    for field, value in update_data.items():
        setattr(parcel, field, value)

    if remarks:
        import uuid
        from app.models.audit_log import AuditLog
        db.add(
            AuditLog(
                log_id=uuid.uuid4(),
                user_id=current_user.id,
                action="UPDATE_PARCEL",
                entity_type="parcel",
                entity_id=parcel.parcel_id,
                old_values={"status": old_status},
                new_values={"status": parcel.status, "remarks": remarks},
                created_at=datetime.utcnow(),
            )
        )

    parcel.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(parcel)

    return _build_parcel_response(db, parcel)


@router.delete(
    "/{parcel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete parcel",
)
def delete_parcel(
    parcel_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_state_or_above),
):
    """Delete a parcel. Requires STATE role or above."""
    stmt = select(Parcel).where(Parcel.parcel_id == parcel_id)
    stmt = _apply_parcel_scope(stmt, current_user)

    parcel = db.execute(stmt).scalar_one_or_none()
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found",
        )

    db.delete(parcel)
    db.commit()


@router.post(
    "/geometry/validate",
    response_model=dict,
    summary="Validate geometry WKT",
)
def validate_geometry(
    geometry_data: ParcelGeometryValidate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Validate a WKT geometry string and return cleaned GeoJSON."""
    try:
        # Check validity
        is_valid = db.execute(
            select(ST_IsValid(ST_GeomFromText(geometry_data.geometry_wkt, 4326)))
        ).scalar()

        result = {"valid": bool(is_valid)}

        if not is_valid:
            # Try to make valid
            fixed_geojson = db.execute(
                select(ST_AsGeoJSON(ST_MakeValid(ST_GeomFromText(geometry_data.geometry_wkt, 4326))))
            ).scalar()
            if fixed_geojson:
                import json
                result["fixed_geometry"] = json.loads(fixed_geojson)
                result["message"] = "Geometry was invalid but has been fixed"
            else:
                result["message"] = "Geometry is invalid and cannot be automatically fixed"
        else:
            # Return as GeoJSON
            geojson = db.execute(
                select(ST_AsGeoJSON(ST_GeomFromText(geometry_data.geometry_wkt, 4326)))
            ).scalar()
            if geojson:
                import json
                result["geometry"] = json.loads(geojson)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid geometry: {str(e)}",
        )


@router.post(
    "/{parcel_id}/transition",
    response_model=dict,
    summary="Transition parcel stage with validation, audit logging, and SLA check",
)
def transition_parcel(
    parcel_id: UUID,
    transition_data: ParcelTransitionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Transition a parcel to a new stage in the acquisition workflow.
    Validates stage transition rules, updates AcquisitionStage record,
    writes an immutable audit log entry, and checks SLA.
    """
    stmt = select(Parcel).where(Parcel.parcel_id == parcel_id)
    stmt = _apply_parcel_scope(stmt, current_user)
    parcel = db.execute(stmt).scalar_one_or_none()
    if not parcel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parcel not found",
        )

    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    result = execute_transition(
        db=db,
        parcel=parcel,
        target_stage=transition_data.target_stage.value,
        acting_user=current_user,
        new_status=transition_data.status.value if transition_data.status else None,
        remarks=transition_data.remarks,
        sla_target_date=transition_data.sla_target_date,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return result


def _build_parcel_response(db: Session, parcel: Parcel) -> ParcelResponse:
    """Build ParcelResponse with geometry and stages."""
    geometry_geojson = _convert_geometry_to_geojson(db, parcel.geometry)
    stages = _build_stages_response(db, parcel.parcel_id)

    return ParcelResponse(
        parcel_id=parcel.parcel_id,
        project_id=parcel.project_id,
        survey_number=parcel.survey_number,
        area_ha=parcel.area_ha,
        geometry=geometry_geojson,
        owner_name=parcel.owner_name,
        owner_reference=parcel.owner_reference,
        current_stage=parcel.current_stage,
        status=parcel.status,
        risk_score=parcel.risk_score,
        village=parcel.village,
        district=parcel.district,
        state=parcel.state,
        assigned_officer=parcel.assigned_officer,
        created_at=parcel.created_at,
        updated_at=parcel.updated_at,
        stages=stages,
    )
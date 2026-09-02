"""FastAPI router for Project CRUD operations."""

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session, selectinload
from geoalchemy2 import Geometry, WKTElement
from geoalchemy2.functions import ST_GeomFromText, ST_AsGeoJSON

from app.core.deps import (
    get_current_user,
    get_user_geographic_scope,
    filter_by_geographic_scope,
    require_district_or_above,
    require_state_or_above,
)
from app.database import get_db
from app.models import Project, Parcel
from app.models.enums import ProjectStatus, UserRole, ParcelStatus
from app.utils.pagination import PageParams, PageResponse, paginate, create_page_response

router = APIRouter()


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)
    states: list[str] = Field(default_factory=list)
    districts: list[str] = Field(default_factory=list)
    land_required_ha: float = Field(default=0.0, ge=0)
    land_acquired_ha: float = Field(default=0.0, ge=0)
    target_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.PLANNING
    corridor_geometry_wkt: Optional[str] = None

    @validator("name", "type", pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            from app.utils.sanitization import sanitize_text
            return sanitize_text(v)
        return v

    @validator("states", "districts", pre=True, each_item=True)
    def sanitize_list_items(cls, v):
        if isinstance(v, str):
            from app.utils.sanitization import sanitize_text
            return sanitize_text(v)
        return v

    @validator("corridor_geometry_wkt", pre=True)
    def validate_corridor_geometry(cls, v):
        if v is not None and isinstance(v, str) and v.strip():
            from app.utils.geo_validation import validate_and_parse_geometry
            validate_and_parse_geometry(v)
        return v


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    states: Optional[list[str]] = None
    districts: Optional[list[str]] = None
    land_required_ha: Optional[float] = Field(None, ge=0)
    land_acquired_ha: Optional[float] = Field(None, ge=0)
    target_date: Optional[date] = None
    status: Optional[ProjectStatus] = None
    corridor_geometry_wkt: Optional[str] = None

    @validator("name", "type", pre=True)
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            from app.utils.sanitization import sanitize_text
            return sanitize_text(v)
        return v

    @validator("states", "districts", pre=True, each_item=True)
    def sanitize_list_items(cls, v):
        if isinstance(v, str):
            from app.utils.sanitization import sanitize_text
            return sanitize_text(v)
        return v

    @validator("corridor_geometry_wkt", pre=True)
    def validate_corridor_geometry(cls, v):
        if v is not None and isinstance(v, str) and v.strip():
            from app.utils.geo_validation import validate_and_parse_geometry
            validate_and_parse_geometry(v)
        return v


class ProjectResponse(BaseModel):
    project_id: UUID
    name: str
    type: str
    states: list[str]
    districts: list[str]
    land_required_ha: float
    land_acquired_ha: float
    target_date: Optional[date]
    status: ProjectStatus
    corridor_geometry: Optional[dict] = None
    created_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    parcels_count: int = 0
    parcels_completed: int = 0

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    project_id: UUID
    name: str
    type: str
    states: list[str]
    districts: list[str]
    land_required_ha: float
    land_acquired_ha: float
    target_date: Optional[date]
    status: ProjectStatus
    created_at: datetime
    parcels_count: int = 0
    parcels_completed: int = 0

    class Config:
        from_attributes = True


class ProjectStatsResponse(BaseModel):
    project_id: UUID
    name: str
    total_parcels: int
    completed_parcels: int
    in_progress_parcels: int
    blocked_parcels: int
    not_started_parcels: int
    land_required_ha: float
    land_acquired_ha: float
    acquisition_progress_pct: float


# ─── Helpers ──────────────────────────────────────────────────────────────────

from datetime import datetime


def _apply_geographic_scope(stmt, user, model):
    """Apply geographic scope filtering based on user's assigned scope."""
    scope = get_user_geographic_scope(user)
    conditions = []

    if scope.get("state"):
        conditions.append(model.state.in_([scope["state"]]))
    if scope.get("district"):
        conditions.append(model.district.in_([scope["district"]]))

    if conditions:
        stmt = stmt.where(and_(*conditions))
    return stmt


def _convert_geometry_to_geojson(geometry_col) -> Optional[dict]:
    """Convert PostGIS geometry to GeoJSON dict."""
    if geometry_col is None:
        return None
    try:
        # This will be handled by the database query
        return geometry_col
    except Exception:
        return None


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_district_or_above),
):
    """Create a new project. Requires DISTRICT role or above."""
    # Validate user can create in their scope
    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and project_data.states:
        for state in project_data.states:
            if state != scope["state"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Cannot create project in state '{state}' outside your scope: {scope['state']}",
                )

    if scope.get("district") and project_data.districts:
        for district in project_data.districts:
            if district != scope["district"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Cannot create project in district '{district}' outside your scope: {scope['district']}",
                )

    # Handle geometry
    geometry = None
    if project_data.corridor_geometry_wkt:
        try:
            geometry = ST_GeomFromText(project_data.corridor_geometry_wkt, 4326)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid geometry WKT: {str(e)}",
            )

    project = Project(
        name=project_data.name,
        type=project_data.type,
        states=project_data.states,
        districts=project_data.districts,
        land_required_ha=project_data.land_required_ha,
        land_acquired_ha=project_data.land_acquired_ha,
        target_date=project_data.target_date,
        status=project_data.status,
        corridor_geometry=geometry,
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return _build_project_response(db, project)


@router.get(
    "",
    response_model=PageResponse[ProjectListResponse],
    summary="List projects with pagination and filters",
)
def list_projects(
    page_params: PageParams = Depends(),
    search: Optional[str] = Query(None, description="Search in name, type"),
    status_filter: Optional[ProjectStatus] = Query(None, alias="status"),
    type_filter: Optional[str] = Query(None, alias="type"),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List projects with pagination, search, and filters. Scope-enforced."""
    stmt = select(Project)

    # Apply geographic scope
    stmt = _apply_geographic_scope(stmt, current_user, Project)

    # Apply filters
    if search:
        search_term = f"%{search}%"
        stmt = stmt.where(
            or_(
                Project.name.ilike(search_term),
                Project.type.ilike(search_term),
            )
        )

    if status_filter:
        stmt = stmt.where(Project.status == status_filter)

    if type_filter:
        stmt = stmt.where(Project.type.ilike(f"%{type_filter}%"))

    if state:
        stmt = stmt.where(Project.states.any(state))

    if district:
        stmt = stmt.where(Project.districts.any(district))

    stmt = stmt.order_by(Project.created_at.desc())

    items, total = paginate(stmt, page_params.page, page_params.page_size, db=db)

    # Build response with parcel counts
    project_ids = [p.project_id for p in items]
    parcel_counts = {}
    if project_ids:
        parcel_stmt = select(
            Parcel.project_id,
            func.count(Parcel.parcel_id).label("total"),
            func.count(Parcel.parcel_id).filter(Parcel.status == "COMPLETED").label("completed"),
        ).where(Parcel.project_id.in_(project_ids)).group_by(Parcel.project_id)

        for row in db.execute(parcel_stmt):
            parcel_counts[row.project_id] = {"total": row.total, "completed": row.completed}

    response_items = []
    for project in items:
        counts = parcel_counts.get(project.project_id, {"total": 0, "completed": 0})
        response_items.append(ProjectListResponse(
            project_id=project.project_id,
            name=project.name,
            type=project.type,
            states=project.states,
            districts=project.districts,
            land_required_ha=project.land_required_ha,
            land_acquired_ha=project.land_acquired_ha,
            target_date=project.target_date,
            status=project.status,
            created_at=project.created_at,
            parcels_count=counts["total"],
            parcels_completed=counts["completed"],
        ))

    return create_page_response(response_items, total, page_params.page, page_params.page_size)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
)
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single project by ID. Scope-enforced."""
    project = db.execute(select(Project).where(Project.project_id == project_id)).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Cross-district / cross-state access -> 403
    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and project.states and scope["state"] not in project.states:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: project outside your state scope '{scope['state']}'",
        )
    if scope.get("district") and project.districts and scope["district"] not in project.districts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: project outside your district scope '{scope['district']}'",
        )

    return _build_project_response(db, project)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
)
def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_district_or_above),
):
    """Update a project. Requires DISTRICT role or above."""
    project = db.execute(select(Project).where(Project.project_id == project_id)).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Cross-district / cross-state check
    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and project.states and scope["state"] not in project.states:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: cannot update project outside your state scope '{scope['state']}'",
        )
    if scope.get("district") and project.districts and scope["district"] not in project.districts:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: cannot update project outside your district scope '{scope['district']}'",
        )

    # Validate scope for updates
    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and project_data.states:
        for state in project_data.states:
            if state != scope["state"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Cannot update project to state '{state}' outside your scope",
                )

    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    geometry_wkt = update_data.pop("corridor_geometry_wkt", None)

    if geometry_wkt is not None:
        if geometry_wkt:
            try:
                project.corridor_geometry = ST_GeomFromText(geometry_wkt, 4326)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid geometry WKT: {str(e)}",
                )
        else:
            project.corridor_geometry = None

    for field, value in update_data.items():
        setattr(project, field, value)

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)

    return _build_project_response(db, project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
)
def delete_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_state_or_above),
):
    """Delete a project. Requires STATE role or above."""
    stmt = select(Project).where(Project.project_id == project_id)
    stmt = _apply_geographic_scope(stmt, current_user, Project)

    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    db.delete(project)
    db.commit()


@router.get(
    "/{project_id}/stats",
    response_model=ProjectStatsResponse,
    summary="Get project statistics",
)
def get_project_stats(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get project statistics and progress metrics."""
    stmt = select(Project).where(Project.project_id == project_id)
    stmt = _apply_geographic_scope(stmt, current_user, Project)

    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Get parcel statistics
    parcel_stats = db.execute(
        select(
            func.count(Parcel.parcel_id).label("total"),
            func.count(Parcel.parcel_id).filter(Parcel.status == "COMPLETED").label("completed"),
            func.count(Parcel.parcel_id).filter(Parcel.status == "IN_PROGRESS").label("in_progress"),
            func.count(Parcel.parcel_id).filter(Parcel.status == "BLOCKED").label("blocked"),
            func.count(Parcel.parcel_id).filter(Parcel.status == "NOT_STARTED").label("not_started"),
        ).where(Parcel.project_id == project_id)
    ).one()

    acquisition_pct = 0.0
    if project.land_required_ha > 0:
        acquisition_pct = (project.land_acquired_ha / project.land_required_ha) * 100

    return ProjectStatsResponse(
        project_id=project.project_id,
        name=project.name,
        total_parcels=parcel_stats.total,
        completed_parcels=parcel_stats.completed,
        in_progress_parcels=parcel_stats.in_progress,
        blocked_parcels=parcel_stats.blocked,
        not_started_parcels=parcel_stats.not_started,
        land_required_ha=project.land_required_ha,
        land_acquired_ha=project.land_acquired_ha,
        acquisition_progress_pct=round(acquisition_pct, 2),
    )


@router.get(
    "/{project_id}/summary",
    summary="Get comprehensive project summary metrics",
)
def get_project_summary(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get rich project summary with stage breakdown, status distribution, and risk metrics."""
    stmt = select(Project).where(Project.project_id == project_id)
    stmt = _apply_geographic_scope(stmt, current_user, Project)

    project = db.execute(stmt).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    status_counts_raw = db.execute(
        select(Parcel.status, func.count(Parcel.parcel_id))
        .where(Parcel.project_id == project_id)
        .group_by(Parcel.status)
    ).all()
    status_dict = {row[0]: row[1] for row in status_counts_raw}

    stage_counts_raw = db.execute(
        select(Parcel.current_stage, func.count(Parcel.parcel_id))
        .where(Parcel.project_id == project_id)
        .group_by(Parcel.current_stage)
    ).all()
    stage_dict = {row[0]: row[1] for row in stage_counts_raw}

    high_risk_count = db.execute(
        select(func.count(Parcel.parcel_id))
        .where(Parcel.project_id == project_id, Parcel.risk_score >= 70.0)
    ).scalar() or 0

    total_parcels = sum(status_dict.values())
    completed = status_dict.get(ParcelStatus.COMPLETED.value, 0)
    in_progress = status_dict.get(ParcelStatus.IN_PROGRESS.value, 0)
    blocked = status_dict.get(ParcelStatus.BLOCKED.value, 0)
    not_started = status_dict.get(ParcelStatus.NOT_STARTED.value, 0)
    disputed = status_dict.get(ParcelStatus.DISPUTED.value, 0)

    acquisition_pct = 0.0
    if project.land_required_ha > 0:
        acquisition_pct = round((project.land_acquired_ha / project.land_required_ha) * 100, 2)

    return {
        "project_id": str(project.project_id),
        "name": project.name,
        "type": project.type,
        "status": project.status,
        "states": project.states,
        "districts": project.districts,
        "land_required_ha": project.land_required_ha,
        "land_acquired_ha": project.land_acquired_ha,
        "acquisition_progress_pct": acquisition_pct,
        "total_parcels": total_parcels,
        "completed_parcels": completed,
        "in_progress_parcels": in_progress,
        "blocked_parcels": blocked,
        "not_started_parcels": not_started,
        "disputed_parcels": disputed,
        "high_risk_parcels": high_risk_count,
        "stages_breakdown": [{"stage": k, "count": v} for k, v in stage_dict.items()],
        "status_breakdown": [{"status": k, "count": v} for k, v in status_dict.items()],
        "target_date": project.target_date.isoformat() if project.target_date else None,
        "created_at": project.created_at.isoformat() if project.created_at else None,
    }


def _build_project_response(db: Session, project: Project) -> ProjectResponse:
    """Build ProjectResponse with parcel counts and geometry."""
    # Get parcel counts
    parcel_stats = db.execute(
        select(
            func.count(Parcel.parcel_id).label("total"),
            func.count(Parcel.parcel_id).filter(Parcel.status == "COMPLETED").label("completed"),
        ).where(Parcel.project_id == project.project_id)
    ).one()

    # Convert geometry to GeoJSON if present
    geometry_geojson = None
    if project.corridor_geometry is not None:
        try:
            geojson_result = db.execute(
                select(ST_AsGeoJSON(project.corridor_geometry))
            ).scalar()
            if geojson_result:
                import json
                geometry_geojson = json.loads(geojson_result)
        except Exception:
            pass

    return ProjectResponse(
        project_id=project.project_id,
        name=project.name,
        type=project.type,
        states=project.states,
        districts=project.districts,
        land_required_ha=project.land_required_ha,
        land_acquired_ha=project.land_acquired_ha,
        target_date=project.target_date,
        status=project.status,
        corridor_geometry=geometry_geojson,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        parcels_count=parcel_stats.total,
        parcels_completed=parcel_stats.completed,
    )


@router.get(
    "/{project_id}/timeline",
    summary="Get unified chronological timeline of events for a project",
    response_model=dict,
)
def get_project_timeline(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict:
    """Return chronological event timeline for the project.

    Merges:
    - Audit log events for the project and its parcels
    - Project history snapshots
    - Stage transition milestones
    """
    project = db.execute(
        select(Project).where(Project.project_id == project_id)
    ).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    timeline_events = []

    # 1. Project creation event
    timeline_events.append({
        "event_id": f"proj-created-{project.project_id}",
        "event_type": "PROJECT_CREATED",
        "timestamp": project.created_at.isoformat() if project.created_at else None,
        "title": f"Project Created: {project.name}",
        "description": f"Targeting {project.land_required_ha:.1f} ha across {len(project.districts)} districts ({', '.join(project.districts[:3])}).",
        "actor_id": str(project.created_by) if project.created_by else None,
        "metadata": {
            "type": project.type,
            "states": project.states,
            "districts": project.districts,
            "target_date": project.target_date.isoformat() if project.target_date else None,
        },
    })

    # 2. Project history snapshots
    from app.models.project_history import ProjectHistory
    snapshots = db.execute(
        select(ProjectHistory)
        .where(ProjectHistory.project_id == project_id)
        .order_by(ProjectHistory.snapshot_date.asc())
    ).scalars().all()

    for snap in snapshots:
        snap_dt = snap.snapshot_date.isoformat() if hasattr(snap.snapshot_date, "isoformat") else str(snap.snapshot_date)
        timeline_events.append({
            "event_id": str(snap.history_id),
            "event_type": "TIMELINE_SNAPSHOT",
            "timestamp": snap_dt,
            "title": f"Monthly Trajectory Snapshot ({snap.parcels_completed}/{snap.parcels_total} parcels completed)",
            "description": f"Acquired {snap.land_acquired_ha:.1f} of {snap.land_required_ha:.1f} ha. In-progress: {snap.parcels_in_progress}, Blocked: {snap.parcels_blocked}.",
            "actor_id": None,
            "metadata": {
                "parcels_total": snap.parcels_total,
                "parcels_completed": snap.parcels_completed,
                "parcels_blocked": snap.parcels_blocked,
                "compensation_paid": float(snap.compensation_paid_total),
                "compensation_pending": float(snap.compensation_pending_total),
            },
        })

    # 3. Audit log events for this project or its parcels
    parcel_ids = db.execute(
        select(Parcel.parcel_id).where(Parcel.project_id == project_id)
    ).scalars().all()

    from app.models.audit_log import AuditLog
    from sqlalchemy import or_

    entity_filters = [
        and_(AuditLog.entity_type == "project", AuditLog.entity_id == project_id)
    ]
    if parcel_ids:
        entity_filters.append(
            and_(AuditLog.entity_type == "parcel", AuditLog.entity_id.in_(parcel_ids[:200]))
        )

    audit_entries = db.execute(
        select(AuditLog)
        .where(or_(*entity_filters))
        .order_by(AuditLog.created_at.desc())
        .limit(100)
    ).scalars().all()

    for a in audit_entries:
        timeline_events.append({
            "event_id": str(a.log_id),
            "event_type": f"AUDIT_{a.action}",
            "timestamp": a.created_at.isoformat() if a.created_at else None,
            "title": f"{a.action.replace('_', ' ').title()} on {a.entity_type.title()}",
            "description": str(a.new_values.get("remarks", "") if a.new_values else ""),
            "actor_id": str(a.user_id) if a.user_id else None,
            "metadata": {
                "entity_type": a.entity_type,
                "entity_id": str(a.entity_id),
                "old_values": a.old_values,
                "new_values": a.new_values,
            },
        })

    # Sort all events chronologically descending (most recent first)
    timeline_events.sort(
        key=lambda e: e["timestamp"] or "",
        reverse=True,
    )

    return {
        "project_id": str(project.project_id),
        "project_name": project.name,
        "total_events": len(timeline_events),
        "timeline": timeline_events,
    }
"""FastAPI router for /reports generation endpoints (TRD §4.10) with strict RBAC."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_user_geographic_scope
from app.database import get_db
from app.models import AcquisitionStage, Compensation, Parcel, Project, RRRecord, User
from app.models.enums import ParcelStatus, StageStatus

router = APIRouter()


def _apply_reports_scope(stmt, user: User, model=Parcel, state_param: Optional[str] = None, district_param: Optional[str] = None):
    """Enforce user's jurisdiction scope on reports queries."""
    scope = get_user_geographic_scope(user)

    clean_state = state_param if isinstance(state_param, str) and state_param.strip() and state_param != "All States" else None
    clean_district = district_param if isinstance(district_param, str) and district_param.strip() and district_param != "All Districts" else None

    if scope.get("state"):
        if clean_state and clean_state.lower() != scope["state"].lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: state '{clean_state}' is outside your jurisdiction '{scope['state']}'",
            )
        if hasattr(model, "state"):
            stmt = stmt.where(func.lower(model.state) == scope["state"].lower())
        elif hasattr(model, "states"):
            stmt = stmt.where(model.states.any(scope["state"]))
    elif clean_state:
        if hasattr(model, "state"):
            stmt = stmt.where(model.state == clean_state)
        elif hasattr(model, "states"):
            stmt = stmt.where(model.states.any(clean_state))

    if scope.get("district"):
        if clean_district and clean_district.lower() != scope["district"].lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: district '{clean_district}' is outside your jurisdiction '{scope['district']}'",
            )
        if hasattr(model, "district"):
            stmt = stmt.where(func.lower(model.district) == scope["district"].lower())
        elif hasattr(model, "districts"):
            stmt = stmt.where(model.districts.any(scope["district"]))
    elif clean_district:
        if hasattr(model, "district"):
            stmt = stmt.where(model.district == clean_district)
        elif hasattr(model, "districts"):
            stmt = stmt.where(model.districts.any(clean_district))

    return stmt


def _generate_executive_html(data: dict) -> str:
    """Generate a clean, professional HTML document for executive presentation."""
    proj = data.get("project", {})
    metrics = data.get("metrics", {})
    stages = data.get("stages", {})
    comp = data.get("compensation", {})
    generated_at = data.get("generated_at", "")

    stages_rows = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #e2e8f0;'>{st}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #e2e8f0;text-align:right;'>{cnt}</td></tr>"
        for st, cnt in stages.items()
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BhoomiSetu — Executive Summary: {proj.get('name', 'Jurisdiction Overview')}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 40px; color: #1e293b; background: #fff; line-height: 1.5; }}
    .header {{ border-bottom: 3px solid #D47A22; padding-bottom: 16px; margin-bottom: 24px; }}
    .badge {{ background: #fef3c7; color: #92400e; padding: 4px 10px; font-weight: 600; font-size: 12px; text-transform: uppercase; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 16px; }}
    .card h4 {{ margin: 0 0 8px 0; color: #64748b; font-size: 13px; text-transform: uppercase; }}
    .card .val {{ font-size: 24px; font-weight: 700; color: #0f172a; margin: 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th {{ background: #f1f5f9; padding: 10px 8px; text-align: left; font-size: 13px; color: #475569; }}
    .section {{ margin-bottom: 32px; }}
    .footer {{ margin-top: 48px; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; padding-top: 16px; }}
</style>
</head>
<body>
    <div class="header">
        <span class="badge">BhoomiSetu Official Statutory Report</span>
        <h1 style="margin: 8px 0 4px 0;">Executive Land Acquisition Summary</h1>
        <p style="margin: 0; color: #64748b;">Project / Scope: <strong>{proj.get('name', 'Portfolio Overview')}</strong> | Status: <strong>{proj.get('status', 'ACTIVE')}</strong></p>
    </div>

    <div class="grid">
        <div class="card">
            <h4>Total Parcels</h4>
            <div class="val">{metrics.get('total_parcels', 0):,}</div>
        </div>
        <div class="card">
            <h4>Land Required</h4>
            <div class="val">{metrics.get('land_required_ha', 0):,.1f} ha</div>
        </div>
        <div class="card">
            <h4>Land Acquired</h4>
            <div class="val">{metrics.get('land_acquired_ha', 0):,.1f} ha</div>
        </div>
        <div class="card">
            <h4>Acquisition %</h4>
            <div class="val">{metrics.get('progress_pct', 0):.1f}%</div>
        </div>
    </div>

    <div class="section">
        <h2 style="font-size: 18px; border-bottom: 1px solid #cbd5e1; padding-bottom: 6px;">Compensation & Disbursement</h2>
        <div class="grid" style="grid-template-columns: repeat(3, 1fr);">
            <div class="card">
                <h4>Approved Amount</h4>
                <div class="val">₹{comp.get('approved_amount', 0):,.0f}</div>
            </div>
            <div class="card">
                <h4>Disbursed (Paid)</h4>
                <div class="val">₹{comp.get('paid_amount', 0):,.0f}</div>
            </div>
            <div class="card">
                <h4>Pending Release</h4>
                <div class="val">₹{comp.get('pending_amount', 0):,.0f}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2 style="font-size: 18px; border-bottom: 1px solid #cbd5e1; padding-bottom: 6px;">Workflow Stage Breakdown</h2>
        <table>
            <thead>
                <tr>
                    <th>Acquisition Workflow Stage</th>
                    <th style="text-align: right;">Active Parcels</th>
                </tr>
            </thead>
            <tbody>
                {stages_rows}
            </tbody>
        </table>
    </div>

    <div class="footer">
        Generated by BhoomiSetu Platform &bull; {generated_at} &bull; Confidential &bull; Official Government Record
    </div>
</body>
</html>"""


@router.get(
    "/executive-summary",
    summary="Generate executive summary report (JSON or HTML)",
)
def get_executive_summary(
    project_id: Optional[UUID] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    format: str = Query("json", pattern="^(json|html)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate high-level executive summary report. Scope-enforced."""
    scope = get_user_geographic_scope(current_user)
    scope_name = district or state or scope.get("district") or scope.get("state") or "National Portfolio"

    clean_pid = project_id if isinstance(project_id, UUID) or (isinstance(project_id, str) and len(str(project_id)) > 10) else None

    proj_info = {"name": f"{scope_name} Overview", "status": "ACTIVE"}
    if clean_pid:
        proj = db.execute(
            select(Project).where(Project.project_id == clean_pid)
        ).scalar_one_or_none()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found.")

        # Verify jurisdiction
        if scope.get("state") and proj.states and scope["state"] not in proj.states:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Project is outside your state jurisdiction '{scope['state']}'",
            )

        proj_info = {
            "project_id": str(proj.project_id),
            "name": proj.name,
            "type": proj.type,
            "status": proj.status,
            "states": proj.states,
            "districts": proj.districts,
        }

    # Parcels query with scope enforcement
    p_stmt = select(
        func.count(Parcel.parcel_id).label("total"),
        func.coalesce(func.sum(Parcel.area_ha), 0.0).label("area"),
        func.coalesce(func.avg(Parcel.risk_score), 0.0).label("avg_risk"),
    )
    if clean_pid:
        p_stmt = p_stmt.where(Parcel.project_id == clean_pid)
    p_stmt = _apply_reports_scope(p_stmt, current_user, model=Parcel, state_param=state, district_param=district)
    p_totals = db.execute(p_stmt).one()

    # Project land
    if clean_pid:
        land_req = float(proj.land_required_ha)
        land_acq = float(proj.land_acquired_ha)
    else:
        l_stmt = select(
            func.coalesce(func.sum(Project.land_required_ha), 0.0),
            func.coalesce(func.sum(Project.land_acquired_ha), 0.0),
        )
        l_stmt = _apply_reports_scope(l_stmt, current_user, model=Project, state_param=state, district_param=district)
        l_totals = db.execute(l_stmt).one()
        land_req = float(l_totals[0])
        land_acq = float(l_totals[1])

    progress_pct = round(land_acq / max(1.0, land_req) * 100, 1)

    # Stages breakdown with scope
    st_stmt = select(Parcel.current_stage, func.count(Parcel.parcel_id))
    if clean_pid:
        st_stmt = st_stmt.where(Parcel.project_id == clean_pid)
    st_stmt = _apply_reports_scope(st_stmt, current_user, model=Parcel, state_param=state, district_param=district)
    stage_counts = dict(db.execute(st_stmt.group_by(Parcel.current_stage)).all())

    # Compensation with scope
    c_stmt = (
        select(
            func.coalesce(func.sum(Compensation.approved_amount), 0.0),
            func.coalesce(func.sum(Compensation.paid_amount), 0.0),
        )
        .join(Parcel, Parcel.parcel_id == Compensation.parcel_id)
    )
    if clean_pid:
        c_stmt = c_stmt.where(Parcel.project_id == clean_pid)
    c_stmt = _apply_reports_scope(c_stmt, current_user, model=Parcel, state_param=state, district_param=district)
    c_row = db.execute(c_stmt).one()
    approved = float(c_row[0])
    paid = float(c_row[1])

    # R&R with scope
    r_stmt = select(func.count(RRRecord.rr_id)).join(Parcel, Parcel.parcel_id == RRRecord.parcel_id)
    if clean_pid:
        r_stmt = r_stmt.where(Parcel.project_id == clean_pid)
    r_stmt = _apply_reports_scope(r_stmt, current_user, model=Parcel, state_param=state, district_param=district)
    total_rr = db.execute(r_stmt).scalar() or 0

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    report_data = {
        "report_title": "Executive Land Acquisition Summary",
        "generated_at": now_iso,
        "project": proj_info,
        "user_jurisdiction": {
            "state": scope.get("state"),
            "district": scope.get("district"),
        },
        "metrics": {
            "total_parcels": p_totals.total,
            "total_parcel_area_ha": round(float(p_totals.area), 2),
            "land_required_ha": round(land_req, 2),
            "land_acquired_ha": round(land_acq, 2),
            "progress_pct": progress_pct,
            "avg_risk_score": round(float(p_totals.avg_risk), 2),
        },
        "stages": stage_counts,
        "compensation": {
            "approved_amount": approved,
            "paid_amount": paid,
            "pending_amount": max(0.0, approved - paid),
            "disbursement_pct": round(paid / max(1.0, approved) * 100, 1),
        },
        "rehabilitation": {
            "total_affected_families": total_rr,
        },
    }

    if format == "html":
        html_content = _generate_executive_html(report_data)
        return HTMLResponse(content=html_content, status_code=200)

    return report_data


@router.get(
    "/projects/{project_id}/pdf-stub",
    summary="Download project executive report as HTML/PDF stub",
)
def download_project_report_stub(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return downloadable HTML document ready for printing or converting to PDF."""
    proj = db.execute(
        select(Project).where(Project.project_id == project_id)
    ).scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found.")

    scope = get_user_geographic_scope(current_user)
    if scope.get("state") and proj.states and scope["state"] not in proj.states:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: Project '{proj.name}' is outside your state jurisdiction",
        )

    report_dict = get_executive_summary(
        project_id=project_id,
        format="json",
        db=db,
        current_user=current_user,
    )
    html = _generate_executive_html(report_dict)

    filename = f"{proj.name.replace(' ', '_')}_executive_summary.html"
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/kpis", summary="KPI metrics for the advanced reporting dashboard")
def get_kpi_metrics(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    project_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return key performance indicators aggregated across accessible parcels. Scope-enforced."""
    q = select(Parcel)
    q = _apply_reports_scope(q, current_user, model=Parcel, state_param=state, district_param=district)

    clean_pid = project_id if isinstance(project_id, UUID) or (isinstance(project_id, str) and len(str(project_id)) > 10) else None

    if clean_pid:
        q = q.where(Parcel.project_id == clean_pid)
    parcels = db.execute(q).scalars().all()

    total = len(parcels)
    completed = sum(1 for p in parcels if p.status == "COMPLETED")
    in_progress = sum(1 for p in parcels if p.status == "IN_PROGRESS")
    blocked = sum(1 for p in parcels if p.status == "BLOCKED")
    disputed = sum(1 for p in parcels if p.status == "DISPUTED")
    total_area = sum(float(p.area_ha or 0) for p in parcels)

    # Compensation
    comp_q = select(
        func.coalesce(func.sum(Compensation.assessed_amount), 0),
        func.coalesce(func.sum(Compensation.approved_amount), 0),
        func.coalesce(func.sum(Compensation.paid_amount), 0),
    ).join(Parcel, Compensation.parcel_id == Parcel.parcel_id)

    comp_q = _apply_reports_scope(comp_q, current_user, model=Parcel, state_param=state, district_param=district)
    if clean_pid:
        comp_q = comp_q.where(Parcel.project_id == clean_pid)

    comp_result = db.execute(comp_q).one()
    assessed, approved, paid = float(comp_result[0]), float(comp_result[1]), float(comp_result[2])

    # Projects count
    proj_q = select(func.count(Project.project_id))
    proj_q = _apply_reports_scope(proj_q, current_user, model=Project, state_param=state, district_param=district)
    proj_count = db.execute(proj_q).scalar() or 0

    return {
        "total_parcels": total,
        "completed_parcels": completed,
        "in_progress_parcels": in_progress,
        "blocked_parcels": blocked,
        "disputed_parcels": disputed,
        "total_area_ha": round(total_area, 2),
        "completion_pct": round(completed / max(1, total) * 100, 1),
        "total_projects": proj_count,
        "compensation": {
            "assessed": round(assessed, 2),
            "approved": round(approved, 2),
            "paid": round(paid, 2),
            "pending": round(max(0, approved - paid), 2),
            "disbursement_pct": round(paid / max(1, approved) * 100, 1),
        },
    }


@router.get("/export/excel", summary="Export report data as Excel-compatible CSV")
def export_report_excel(
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    project_id: Optional[UUID] = Query(None),
    stage: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export filtered parcel data as CSV (Excel-compatible). Scope-enforced."""
    q = select(Parcel)
    q = _apply_reports_scope(q, current_user, model=Parcel, state_param=state, district_param=district)

    if project_id:
        q = q.where(Parcel.project_id == project_id)
    if stage:
        q = q.where(Parcel.current_stage == stage)
    if status_filter:
        q = q.where(Parcel.status == status_filter)

    parcels = db.execute(q).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Parcel ID", "Survey Number", "Village", "District", "State",
        "Owner Name", "Area (Ha)", "Current Stage", "Status",
        "Risk Score", "Created At",
    ])
    for p in parcels:
        writer.writerow([
            str(p.parcel_id), p.survey_number, p.village, p.district, p.state,
            p.owner_name or "N/A", float(p.area_ha or 0), p.current_stage, p.status,
            float(p.risk_score or 0),
            p.created_at.isoformat() if p.created_at else "",
        ])

    csv_content = output.getvalue()
    filename = f"bhoomisetu_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

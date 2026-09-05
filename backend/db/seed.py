"""Database seeder supporting procedural demo generation and synthetic CSV ingestion.

Usage:
  python backend/db/seed.py --source demo
  python backend/db/seed.py --source synthetic
  python backend/db/seed.py --reset --source synthetic
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# Ensure backend root is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from geoalchemy2.elements import WKTElement
from sqlalchemy import select, text

from app.config import get_settings
from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
from app.models import (
    AcquisitionStage,
    AuditLog,
    Compensation,
    GISBoundary,
    Project,
    ProjectHistory,
    RRRecord,
    User,
)
from app.models.enums import (
    AffectedType,
    CompensationPaymentStatus,
    ParcelStatus,
    ProjectStatus,
    RehabilitationStatus,
    StageName,
    StageStatus,
    UserRole,
)
from app.models.parcel import Parcel
from app.services.transition import STAGE_ORDER

settings = get_settings()

# ── Geographic Helpers ────────────────────────────────────────────────────────

DISTRICT_CONFIGS = [
    {
        "state": "Maharashtra",
        "district": "Pune",
        "center_lat": 18.5204,
        "center_lon": 73.8567,
        "villages": ["Wagholi", "Maan", "Hinjawadi", "Hadapsar", "Chakan", "Bavdhan", "Kharadi", "Loni Kalbhor", "Pirangut", "Khed"],
    },
    {
        "state": "Maharashtra",
        "district": "Thane",
        "center_lat": 19.2183,
        "center_lon": 72.9781,
        "villages": ["Kalyan", "Dombivli", "Bhiwandi", "Mumbra", "Badlapur", "Ambarnath", "Shahapur", "Murbad"],
    },
    {
        "state": "Maharashtra",
        "district": "Raigad",
        "center_lat": 18.5158,
        "center_lon": 73.1822,
        "villages": ["Panvel", "Pen", "Uran", "Karjat", "Khalapur", "Alibag", "Roha", "Mangaon"],
    },
    {
        "state": "Maharashtra",
        "district": "Palghar",
        "center_lat": 19.6967,
        "center_lon": 72.7699,
        "villages": ["Dahanu", "Palghar", "Wada", "Talasari", "Jawhar", "Vikramgad", "Mokhada", "Vasai"],
    },
    {
        "state": "Rajasthan",
        "district": "Jaipur",
        "center_lat": 26.9124,
        "center_lon": 75.7873,
        "villages": ["Sanganer", "Amber", "Bassi", "Chaksu", "Kotputli", "Shahpura", "Phulera", "Jamwa Ramgarh"],
    },
    {
        "state": "Rajasthan",
        "district": "Jodhpur",
        "center_lat": 26.2389,
        "center_lon": 73.0243,
        "villages": ["Osian", "Bilara", "Luni", "Bhopalgarh", "Shergarh", "Balesar", "Phalodi", "Piparcity"],
    },
    {
        "state": "Uttar Pradesh",
        "district": "Moradabad",
        "center_lat": 28.8386,
        "center_lon": 78.7733,
        "villages": ["Peepli Khadder", "Kanth", "Bilari", "Thakurdwara"],
    },
    {
        "state": "Uttar Pradesh",
        "district": "Bahraich",
        "center_lat": 27.5705,
        "center_lon": 81.5977,
        "villages": ["Madh Nagar", "Khasaha Mohammadpur", "Nanpara", "Mahasi"],
    },
    {
        "state": "Uttar Pradesh",
        "district": "Sitapur",
        "center_lat": 27.5684,
        "center_lon": 80.6829,
        "villages": ["Saholi", "Kurriya Udaipur", "Karkhila", "Biswan"],
    },
]

FIRST_NAMES = [
    "Ramesh", "Suresh", "Rajesh", "Sunita", "Ananya", "Mohanlal", "Ganesh", "Pooja",
    "Vikram", "Deepak", "Kavita", "Sanjay", "Santosh", "Prakash", "Amit", "Rahul",
    "Priyanka", "Nitin", "Mahesh", "Kishore", "Vijay", "Balasaheb", "Chandrakant",
    "Jyoti", "Laxman", "Subhash", "Manish", "Dattatray", "Ashok", "Pandurang",
]

LAST_NAMES = [
    "Patil", "Deshmukh", "Sharma", "Gaikwad", "Gupta", "Joshi", "Shinde", "Pawar",
    "Chavan", "Kulkarni", "Jadhav", "More", "Bhosale", "Shekhawat", "Choudhary",
    "Rathore", "Bishnoi", "Meena", "Tambe", "Kadam", "Sawant", "Ghate", "Mane", "Wagh",
]


def generate_polygon_wkt(center_lat: float, center_lon: float, offset_idx: int) -> str:
    """Generate a small realistic polygon near the center point."""
    lat_offset = ((offset_idx % 40) - 20) * 0.003 + random.uniform(-0.001, 0.001)
    lon_offset = ((offset_idx // 40) - 20) * 0.003 + random.uniform(-0.001, 0.001)

    lat = center_lat + lat_offset
    lon = center_lon + lon_offset

    d = random.uniform(0.0008, 0.0025)
    p1 = f"{lon:.6f} {lat:.6f}"
    p2 = f"{lon + d:.6f} {lat + d*0.2:.6f}"
    p3 = f"{lon + d*0.9:.6f} {lat + d*1.1:.6f}"
    p4 = f"{lon - d*0.1:.6f} {lat + d*0.9:.6f}"
    return f"POLYGON(({p1}, {p2}, {p3}, {p4}, {p1}))"


def generate_corridor_wkt(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Generate a LineString corridor geometry."""
    mid_lat = (lat1 + lat2) / 2 + random.uniform(-0.05, 0.05)
    mid_lon = (lon1 + lon2) / 2 + random.uniform(-0.05, 0.05)
    return f"LINESTRING({lon1:.6f} {lat1:.6f}, {mid_lon:.6f} {mid_lat:.6f}, {lon2:.6f} {lat2:.6f})"


def generate_multipolygon_wkt(lat: float, lon: float, size: float = 0.25) -> str:
    """Generate a MultiPolygon boundary box for a district or state."""
    p1 = f"{lon - size:.6f} {lat - size:.6f}"
    p2 = f"{lon + size:.6f} {lat - size:.6f}"
    p3 = f"{lon + size:.6f} {lat + size:.6f}"
    p4 = f"{lon - size:.6f} {lat + size:.6f}"
    return f"MULTIPOLYGON((({p1}, {p2}, {p3}, {p4}, {p1})))"


def deterministic_uuid(prefix: str, key: str) -> uuid.UUID:
    """Produce deterministic, repeatable UUIDs from string keys."""
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"bhoomisetu:{prefix}:{key.strip()}")


# ── Database Reset ────────────────────────────────────────────────────────────

def reset_database(db) -> None:
    """Safely wipe existing records in child-to-parent order."""
    print("   [RESET] Truncating existing tables...")
    tables = [
        "audit_logs",
        "alerts",
        "documents",
        "project_history",
        "rr_records",
        "compensation",
        "acquisition_stages",
        "parcels",
        "projects",
        "gis_boundaries",
        "refresh_tokens",
        "users",
    ]
    for table in tables:
        try:
            db.execute(text(f"DELETE FROM {table}"))
        except Exception:
            pass
    db.commit()
    print("   [OK] Tables cleared.")


# ── Core Seeders ──────────────────────────────────────────────────────────────

def seed_users(db) -> dict[str, User]:
    """Seed the 6 canonical demo users with standard credentials."""
    print("\n--- Seeding 6 Demo Users (One per role) ---")
    password_plain = "password123"
    pwd_hash = hash_password(password_plain)

    demo_users_data = [
        {
            "username": "admin",
            "email": "admin@bhoomisetu.gov.in",
            "role": UserRole.ADMIN.value,
            "state_scope": None,
            "district_scope": None,
        },
        {
            "username": "central_user",
            "email": "central@bhoomisetu.gov.in",
            "role": UserRole.CENTRAL.value,
            "state_scope": None,
            "district_scope": None,
        },
        {
            "username": "state_user",
            "email": "state.up@bhoomisetu.gov.in",
            "role": UserRole.STATE.value,
            "state_scope": "Uttar Pradesh",
            "district_scope": None,
        },
        {
            "username": "district_user",
            "email": "collector.ghaziabad@bhoomisetu.gov.in",
            "role": UserRole.DISTRICT.value,
            "state_scope": "Uttar Pradesh",
            "district_scope": "Ghaziabad",
        },
        {
            "username": "agency_user",
            "email": "nhai.agency@bhoomisetu.gov.in",
            "role": UserRole.PROJECT_AGENCY.value,
            "state_scope": "Uttar Pradesh",
            "district_scope": "Ghaziabad",
        },
        {
            "username": "field_officer",
            "email": "officer.ghaziabad@bhoomisetu.gov.in",
            "role": UserRole.FIELD_OFFICER.value,
            "state_scope": "Uttar Pradesh",
            "district_scope": "Ghaziabad",
        },
    ]

    user_map: dict[str, User] = {}
    for udata in demo_users_data:
        existing = db.execute(select(User).where(User.username == udata["username"])).scalar_one_or_none()
        if not existing:
            u = User(
                id=deterministic_uuid("user", udata["username"]),
                username=udata["username"],
                email=udata["email"],
                password_hash=pwd_hash,
                role=udata["role"],
                state_scope=udata["state_scope"],
                district_scope=udata["district_scope"],
                is_active=True,
            )
            db.add(u)
            user_map[udata["username"]] = u
            print(f"   + Created user: {udata['username']:<15} [Role: {udata['role']}]")
        else:
            user_map[udata["username"]] = existing
            print(f"   = Existing user: {udata['username']:<15}")

    db.commit()
    for u in user_map.values():
        db.refresh(u)
    return user_map


def seed_boundaries(db) -> None:
    """Seed administrative GIS boundaries (State, District, Village polygons)."""
    print("\n--- Seeding Administrative Boundaries ---")
    boundary_entries = [
        {"level": "state", "name": "Maharashtra", "parent": "India", "state": "Maharashtra", "dist": None, "lat": 19.7515, "lon": 75.7139, "size": 1.5},
        {"level": "state", "name": "Rajasthan", "parent": "India", "state": "Rajasthan", "dist": None, "lat": 27.0238, "lon": 74.2179, "size": 1.5},
        {"level": "state", "name": "Uttar Pradesh", "parent": "India", "state": "Uttar Pradesh", "dist": None, "lat": 26.8467, "lon": 80.9462, "size": 1.6},
        {"level": "state", "name": "Gujarat", "parent": "India", "state": "Gujarat", "dist": None, "lat": 22.2587, "lon": 71.1924, "size": 1.2},
        {"level": "district", "name": "Pune", "parent": "Maharashtra", "state": "Maharashtra", "dist": "Pune", "lat": 18.5204, "lon": 73.8567, "size": 0.4},
        {"level": "district", "name": "Thane", "parent": "Maharashtra", "state": "Maharashtra", "dist": "Thane", "lat": 19.2183, "lon": 72.9781, "size": 0.3},
        {"level": "district", "name": "Raigad", "parent": "Maharashtra", "state": "Maharashtra", "dist": "Raigad", "lat": 18.5158, "lon": 73.1822, "size": 0.35},
        {"level": "district", "name": "Palghar", "parent": "Maharashtra", "state": "Maharashtra", "dist": "Palghar", "lat": 19.6967, "lon": 72.7699, "size": 0.35},
        {"level": "district", "name": "Jaipur", "parent": "Rajasthan", "state": "Rajasthan", "dist": "Jaipur", "lat": 26.9124, "lon": 75.7873, "size": 0.4},
        {"level": "district", "name": "Jodhpur", "parent": "Rajasthan", "state": "Rajasthan", "dist": "Jodhpur", "lat": 26.2389, "lon": 73.0243, "size": 0.45},
        {"level": "district", "name": "Moradabad", "parent": "Uttar Pradesh", "state": "Uttar Pradesh", "dist": "Moradabad", "lat": 28.8386, "lon": 78.7733, "size": 0.35},
        {"level": "district", "name": "Bahraich", "parent": "Uttar Pradesh", "state": "Uttar Pradesh", "dist": "Bahraich", "lat": 27.5705, "lon": 81.5977, "size": 0.35},
        {"level": "district", "name": "Sitapur", "parent": "Uttar Pradesh", "state": "Uttar Pradesh", "dist": "Sitapur", "lat": 27.5684, "lon": 80.6829, "size": 0.35},
    ]

    for dcfg in DISTRICT_CONFIGS:
        for vname in dcfg["villages"][:3]:
            boundary_entries.append({
                "level": "village",
                "name": vname,
                "parent": dcfg["district"],
                "state": dcfg["state"],
                "dist": dcfg["district"],
                "lat": dcfg["center_lat"] + random.uniform(-0.04, 0.04),
                "lon": dcfg["center_lon"] + random.uniform(-0.04, 0.04),
                "size": 0.04,
            })

    existing_count = db.execute(select(GISBoundary)).scalars().all()
    if len(existing_count) < len(boundary_entries):
        for b in boundary_entries:
            geom_wkt = generate_multipolygon_wkt(b["lat"], b["lon"], b["size"])
            boundary = GISBoundary(
                boundary_id=deterministic_uuid("bnd", f"{b['level']}:{b['name']}"),
                level=b["level"],
                name=b["name"],
                parent_name=b["parent"],
                state_name=b["state"],
                district_name=b["dist"],
                geometry=WKTElement(geom_wkt, srid=4326),
            )
            db.add(boundary)
        db.commit()
        print(f"   [OK] Seeded {len(boundary_entries)} administrative boundaries.")
    else:
        print(f"   [INFO] {len(existing_count)} boundaries already present.")


# ── Synthetic CSV Ingestion Seeder ───────────────────────────────────────────

SYNTHETIC_STAGE_MAPPING = {
    "Land Identification": StageName.IDENTIFICATION.value,
    "Survey/Parcel Mapping": StageName.SURVEY.value,
    "Ownership Verification": StageName.VERIFICATION.value,
    "Notification": StageName.NOTIFICATION.value,
    "Objections/Hearings": StageName.OBJECTION.value,
    "Declaration": StageName.NOTIFICATION.value,
    "Compensation Assessment": StageName.AWARD.value,
    "Award Enquiry": StageName.AWARD.value,
    "Compensation Disbursement": StageName.COMPENSATION.value,
    "Rehabilitation & Resettlement": StageName.REHABILITATION_RESETTLEMENT.value,
    "Possession": StageName.POSSESSION.value,
    "Land Transfer/Mutation": StageName.POSSESSION.value,
    "Closure/Handover": StageName.CLOSURE.value,
    "Closure": StageName.CLOSURE.value,
}


def seed_from_synthetic(db, user_map: dict[str, User], data_dir: Path) -> None:
    """Ingest canonical synthetic dataset from data/synthetic CSVs and GeoJSON."""
    print(f"\n--- Ingesting Synthetic Dataset from {data_dir} ---")
    admin_user = user_map["admin"]
    field_user = user_map["field_officer"]

    # 1. Projects
    projects_csv = data_dir / "projects.csv"
    if not projects_csv.exists():
        raise FileNotFoundError(f"Missing synthetic projects file: {projects_csv}")

    print("1. Ingesting projects.csv...")
    project_id_map: dict[str, uuid.UUID] = {}
    projects_to_insert = []

    with open(projects_csv, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            raw_id = row["project_id"]
            p_uuid = deterministic_uuid("prj", raw_id)
            project_id_map[raw_id] = p_uuid

            state = row.get("state", "Uttar Pradesh")
            land_req = float(row.get("land_required_ha", 50.0))
            corridor_wkt = generate_corridor_wkt(27.0 + (idx * 0.2), 80.0 + (idx * 0.1), 27.5 + (idx * 0.2), 80.8 + (idx * 0.1))

            proj_dist = row["name"].split(" Project")[0].split(" Urban")[0].split(" Industrial")[0].split(" Power")[0].split(" Irrigation")[0].split(" Rural")[0].split(" Railway")[0].strip()
            p = Project(
                project_id=p_uuid,
                name=row["name"],
                type=row.get("type", "Highway"),
                states=[state],
                districts=[proj_dist],
                land_required_ha=land_req,
                land_acquired_ha=round(land_req * 0.45, 2),
                target_date=date.today() + timedelta(days=int(row.get("target_days", 365))),
                status=ProjectStatus.ACTIVE.value,
                corridor_geometry=WKTElement(corridor_wkt, srid=4326),
                created_by=admin_user.id,
            )
            projects_to_insert.append(p)
            db.merge(p)

    db.commit()
    print(f"   [OK] Ingested {len(projects_to_insert)} projects.")

    # 2. GeoJSON Geometry lookup
    geojson_path = data_dir / "parcels_geometry.geojson"
    geometry_lookup: dict[str, str] = {}
    properties_lookup: dict[str, dict] = {}
    if geojson_path.exists():
        print("2. Parsing parcels_geometry.geojson for spatial bounds...")
        try:
            with open(geojson_path, mode="r", encoding="utf-8") as f:
                gdata = json.load(f)
                for feat in gdata.get("features", []):
                    props = feat.get("properties", {})
                    pid = props.get("parcel_id")
                    if pid:
                        properties_lookup[pid] = props
                        geom = feat.get("geometry", {})
                        coords = geom.get("coordinates", [])
                        if coords and len(coords[0]) >= 3:
                            ring = ", ".join([f"{pt[0]:.6f} {pt[1]:.6f}" for pt in coords[0]])
                            geometry_lookup[pid] = f"POLYGON(({ring}))"
            print(f"   [OK] Cached geometry for {len(geometry_lookup)} parcels.")
        except Exception as e:
            print(f"   [WARN] Could not parse parcels_geometry.geojson ({e}). Proceeding without cached geometry.")

    # 3. Project-Parcel Links
    links_csv = data_dir / "project_parcel_links.csv"
    parcel_to_project: dict[str, str] = {}
    if links_csv.exists():
        with open(links_csv, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                parcel_to_project[row["parcel_id"]] = row["project_id"]

    # 4. Disputes
    disputes_csv = data_dir / "disputes.csv"
    disputed_parcels = set()
    if disputes_csv.exists():
        with open(disputes_csv, mode="r", encoding="utf-8") as f:
            for d_row in csv.DictReader(f):
                disputed_parcels.add(d_row["parcel_id"])

    # 5. Parcels & Stages
    status_csv = data_dir / "parcel_current_status.csv"
    print("3. Ingesting parcels and acquisition stages...")
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()

    seeded_parcels = 0
    with open(status_csv, mode="r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for idx, row in enumerate(rows):
        raw_pid = row["parcel_id"]
        raw_prjid = row.get("project_id") or parcel_to_project.get(raw_pid, "PRJ-001")
        pr_uuid = project_id_map.get(raw_prjid, list(project_id_map.values())[0])
        parcel_uuid = deterministic_uuid("pcl", raw_pid)

        # Geometrics & metadata
        props = properties_lookup.get(raw_pid, {})
        village = props.get("village", f"Village-{idx % 10 + 1}")
        district = props.get("district", "Moradabad")
        state = props.get("state", "Uttar Pradesh")
        survey_no = props.get("survey_number", f"{100 + idx}/1")
        area_ha = float(props.get("area_hectare", 0.5))

        wkt_geom = geometry_lookup.get(raw_pid, generate_polygon_wkt(27.5, 80.5, idx))

        # Workflow status & stage
        raw_stage = row.get("stage", "Survey/Parcel Mapping")
        stage_mapped = SYNTHETIC_STAGE_MAPPING.get(raw_stage, StageName.SURVEY.value)
        is_disputed = raw_pid in disputed_parcels
        is_possession_or_closure = stage_mapped in (StageName.CLOSURE.value, StageName.POSSESSION.value)

        if is_disputed:
            p_status = ParcelStatus.BLOCKED.value
            risk = round(random.uniform(76.0, 94.5), 1)
        elif is_possession_or_closure:
            p_status = ParcelStatus.COMPLETED.value
            risk = round(random.uniform(5.0, 14.5), 1)
        else:
            p_status = ParcelStatus.IN_PROGRESS.value
            high_risk_prob = 0.45 if raw_prjid in ("PRJ-003", "PRJ-007", "PRJ-009", "PRJ-023") else 0.28
            if random.random() < high_risk_prob:
                risk = round(random.uniform(70.0, 88.5), 1)
            else:
                risk = round(random.uniform(18.0, 64.0), 1)

        owner = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        parcel = Parcel(
            parcel_id=parcel_uuid,
            project_id=pr_uuid,
            survey_number=survey_no,
            area_ha=area_ha,
            geometry=WKTElement(wkt_geom, srid=4326),
            owner_name=owner,
            owner_reference=f"UID-{1000 + (idx % 8999)}-{random.randint(1000, 9999)}",
            current_stage=stage_mapped,
            status=p_status,
            risk_score=risk,
            village=village,
            district=district,
            state=state,
            assigned_officer=field_user.id if random.random() < 0.75 else None,
            created_at=now_utc - timedelta(days=int(row.get("days_in_stage", 30)) + 60),
        )
        db.merge(parcel)
        seeded_parcels += 1

        # Stages (1 to 11)
        stage_idx = [s.value for s in STAGE_ORDER].index(stage_mapped)
        for s_order, s_enum in enumerate(STAGE_ORDER, start=1):
            s_name = s_enum.value
            if s_order <= stage_idx:
                s_status = StageStatus.COMPLETED.value
                s_start = today - timedelta(days=(stage_idx - s_order + 1) * 30 + 15)
                s_target = s_start + timedelta(days=30)
                s_comp = s_start + timedelta(days=25)
            elif s_order == stage_idx + 1:
                is_breached = (p_status == ParcelStatus.BLOCKED.value) or (risk >= 70.0)
                s_status = StageStatus.BLOCKED.value if is_breached else StageStatus.IN_PROGRESS.value
                s_start = today - timedelta(days=min(180, int(row.get("days_in_stage", 15))))
                s_target = s_start + timedelta(days=int(row.get("sla_days", 30)))
                s_comp = None
            else:
                s_status = StageStatus.NOT_STARTED.value
                s_start, s_target, s_comp = None, None, None

            stg = AcquisitionStage(
                stage_id=deterministic_uuid("stg", f"{raw_pid}:{s_name}"),
                parcel_id=parcel_uuid,
                stage_name=s_name,
                stage_order=s_order,
                start_date=s_start,
                target_date=s_target,
                completion_date=s_comp,
                status=s_status,
                assigned_officer=field_user.id,
                remarks="Ingested from synthetic dataset.",
            )
            db.merge(stg)

    db.commit()
    print(f"   [OK] Ingested {seeded_parcels} parcels and their full 11-stage histories.")

    # 5. Compensation
    comp_csv = data_dir / "compensation.csv"
    if comp_csv.exists():
        print("4. Ingesting compensation.csv records...")
        c_count = 0
        with open(comp_csv, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                p_uuid = deterministic_uuid("pcl", row["parcel_id"])
                assessed = float(row.get("assessed_amount", 1000000.0))
                approved = float(row.get("approved_amount", assessed))
                paid = float(row.get("paid_amount", 0.0))

                raw_stat = row.get("payment_status", "pending").lower()
                if raw_stat == "paid":
                    p_stat = CompensationPaymentStatus.DISBURSED.value
                elif raw_stat == "partial":
                    p_stat = CompensationPaymentStatus.PARTIALLY_PAID.value
                else:
                    p_stat = CompensationPaymentStatus.APPROVED.value

                comp = Compensation(
                    compensation_id=deterministic_uuid("cmp", row["parcel_id"]),
                    parcel_id=p_uuid,
                    assessed_amount=assessed,
                    approved_amount=approved,
                    paid_amount=paid,
                    payment_status=p_stat,
                    payment_date=today - timedelta(days=15) if p_stat == CompensationPaymentStatus.DISBURSED.value else None,
                    remarks="Calculated per RFCTLARR 2013 statutory rules.",
                )
                db.merge(comp)
                c_count += 1
        db.commit()
        print(f"   [OK] Ingested {c_count} compensation records.")

    # 6. R&R Records
    rr_csv = data_dir / "rehabilitation_resettlement.csv"
    if rr_csv.exists():
        print("5. Ingesting rehabilitation_resettlement.csv...")
        rr_count = 0
        with open(rr_csv, mode="r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                p_uuid = deterministic_uuid("pcl", row["parcel_id"])
                paf_type_raw = row.get("paf_type", "title_holder").upper()
                if "TITLE" in paf_type_raw:
                    paf_type = AffectedType.TITLE_HOLDER.value
                elif "TENANT" in paf_type_raw:
                    paf_type = AffectedType.TENANT.value
                else:
                    paf_type = AffectedType.AGRICULTURAL_LABOURER.value

                rr = RRRecord(
                    rr_id=deterministic_uuid("rr", row.get("rr_id", str(uuid.uuid4()))),
                    parcel_id=p_uuid,
                    paf_name=row.get("paf_name", "Affected Landowner"),
                    paf_type=paf_type,
                    family_size=int(row.get("family_size", 4)),
                    affected_area_ha=0.4,
                    rehabilitation_status=RehabilitationStatus.PLAN_APPROVED.value,
                    compensation_paid=float(row.get("cash_grant_paid", 50000.0)),
                    relocation_site=row.get("allotted_house_site", "Model Resettlement Colony"),
                    plot_allotted=f"Plot-{random.randint(101, 899)}",
                )
                db.merge(rr)
                rr_count += 1
        db.commit()
        print(f"   [OK] Ingested {rr_count} R&R records.")

    # 7. Project History Snapshots
    hist_csv = data_dir / "project_history_snapshots.csv"
    if hist_csv.exists():
        print("6. Ingesting project_history_snapshots.csv...")
        h_count = 0
        with open(hist_csv, mode="r", encoding="utf-8") as f:
            for idx, row in enumerate(csv.DictReader(f)):
                raw_prjid = row["project_id"]
                pr_uuid = project_id_map.get(raw_prjid)
                if not pr_uuid:
                    continue

                snap = ProjectHistory(
                    snapshot_id=deterministic_uuid("snap", f"{raw_prjid}:{row['snapshot_date']}:{idx}"),
                    project_id=pr_uuid,
                    snapshot_date=datetime.strptime(row["snapshot_date"], "%Y-%m-%d").date(),
                    land_required_ha=100.0,
                    land_acquired_ha=float(row.get("completed_parcels", 10)) * 0.5,
                    parcels_total=int(row.get("pending_parcels", 20)) + int(row.get("completed_parcels", 10)),
                    parcels_completed=int(row.get("completed_parcels", 10)),
                    parcels_in_progress=int(row.get("pending_parcels", 20)),
                    parcels_disputed=int(row.get("sla_breaches", 2)),
                    compensation_paid_total=float(row.get("completed_parcels", 10)) * 1500000.0,
                    compensation_pending_total=float(row.get("compensation_pending", 5)) * 1500000.0,
                    stages_snapshot={
                        "SURVEY": 5,
                        "VERIFICATION": 4,
                        "AWARD": 3,
                        "COMPENSATION": int(row.get("compensation_pending", 2)),
                    },
                    metadata_json={
                        "pending_parcels": float(row.get("pending_parcels", 10)),
                        "completed_parcels": float(row.get("completed_parcels", 10)),
                        "average_stage_days": float(row.get("average_stage_days", 45.0)),
                        "sla_breaches": float(row.get("sla_breaches", 2)),
                        "compensation_pending": float(row.get("compensation_pending", 3)),
                        "rr_pending": float(row.get("rr_pending", 2)),
                        "possession_pending": float(row.get("possession_pending", 1)),
                        "processing_rate": float(row.get("processing_rate", 0.15)),
                        "officers_count": 4,
                    },
                )
                db.merge(snap)
                h_count += 1
        db.commit()
        print(f"   [OK] Ingested {h_count} historical snapshots.")


# ── Procedural Demo Seeder ───────────────────────────────────────────────────

def seed_demo(db, user_map: dict[str, User]) -> None:
    """Generate 6 rich multi-state infrastructure projects and 2,220 parcels."""
    print("\n--- Generating Procedural Demo Corridors (Phases 1-3) ---")
    admin_user = user_map["admin"]
    field_user = user_map["field_officer"]

    projects_data = [
        {
            "name": "Delhi-Mumbai Expressway (Vadodara-Mumbai Section)",
            "type": "Highway",
            "states": ["Maharashtra", "Gujarat"],
            "districts": ["Thane", "Palghar", "Raigad"],
            "land_required_ha": 850.0,
            "land_acquired_ha": 520.4,
            "target_date": date(2027, 3, 31),
            "status": ProjectStatus.ACTIVE.value,
            "lat1": 19.2, "lon1": 73.0, "lat2": 20.5, "lon2": 72.9,
        },
        {
            "name": "Pune Ring Road (Eastern & Western Alignment)",
            "type": "Highway",
            "states": ["Maharashtra"],
            "districts": ["Pune"],
            "land_required_ha": 620.0,
            "land_acquired_ha": 280.5,
            "target_date": date(2026, 12, 31),
            "status": ProjectStatus.ACTIVE.value,
            "lat1": 18.4, "lon1": 73.7, "lat2": 18.7, "lon2": 74.0,
        },
        {
            "name": "Mumbai-Ahmedabad High Speed Rail (MAHSR Bullet Train)",
            "type": "Railway",
            "states": ["Maharashtra", "Gujarat"],
            "districts": ["Thane", "Palghar"],
            "land_required_ha": 430.0,
            "land_acquired_ha": 395.0,
            "target_date": date(2026, 8, 15),
            "status": ProjectStatus.ACTIVE.value,
            "lat1": 19.15, "lon1": 72.85, "lat2": 20.0, "lon2": 72.8,
        },
        {
            "name": "Western Dedicated Freight Corridor (WDFC - Phase 2)",
            "type": "Railway",
            "states": ["Rajasthan", "Maharashtra"],
            "districts": ["Jaipur", "Jodhpur", "Thane"],
            "land_required_ha": 750.0,
            "land_acquired_ha": 410.0,
            "target_date": date(2027, 6, 30),
            "status": ProjectStatus.ACTIVE.value,
            "lat1": 26.9, "lon1": 75.8, "lat2": 26.2, "lon2": 73.0,
        },
        {
            "name": "Jaipur Ring Road & Multimodal Logistics Hub",
            "type": "Industrial",
            "states": ["Rajasthan"],
            "districts": ["Jaipur"],
            "land_required_ha": 380.0,
            "land_acquired_ha": 95.0,
            "target_date": date(2028, 1, 31),
            "status": ProjectStatus.PLANNING.value,
            "lat1": 26.85, "lon1": 75.7, "lat2": 27.05, "lon2": 75.9,
        },
        {
            "name": "JNPT Port Container Expansion & Coastal Highway",
            "type": "Port",
            "states": ["Maharashtra"],
            "districts": ["Raigad", "Thane"],
            "land_required_ha": 290.0,
            "land_acquired_ha": 245.0,
            "target_date": date(2026, 11, 30),
            "status": ProjectStatus.ACTIVE.value,
            "lat1": 18.95, "lon1": 72.95, "lat2": 18.8, "lon2": 73.05,
        },
    ]

    created_projects: list[Project] = []
    for pdata in projects_data:
        existing = db.execute(select(Project).where(Project.name == pdata["name"])).scalar_one_or_none()
        if not existing:
            corridor_wkt = generate_corridor_wkt(pdata["lat1"], pdata["lon1"], pdata["lat2"], pdata["lon2"])
            proj = Project(
                project_id=deterministic_uuid("prj", pdata["name"]),
                name=pdata["name"],
                type=pdata["type"],
                states=pdata["states"],
                districts=pdata["districts"],
                land_required_ha=pdata["land_required_ha"],
                land_acquired_ha=pdata["land_acquired_ha"],
                target_date=pdata["target_date"],
                status=pdata["status"],
                corridor_geometry=WKTElement(corridor_wkt, srid=4326),
                created_by=admin_user.id,
            )
            db.add(proj)
            created_projects.append(proj)
            print(f"   + Created project: {proj.name}")
        else:
            created_projects.append(existing)
            print(f"   = Existing project: {existing.name}")

    db.commit()
    for p in created_projects:
        db.refresh(p)

    print("\n--- Generating 2,220 Synthetic Parcels across Projects ---")
    parcels_per_project = 370
    stage_choices = [s.value for s in STAGE_ORDER]
    stage_weights = [0.08, 0.10, 0.12, 0.12, 0.14, 0.10, 0.10, 0.08, 0.06, 0.06, 0.04]
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()

    for proj in created_projects:
        matching_districts = [d for d in DISTRICT_CONFIGS if d["district"] in proj.districts or d["state"] in proj.states]
        if not matching_districts:
            matching_districts = DISTRICT_CONFIGS[:2]

        p_batch, s_batch, c_batch, rr_batch = [], [], [], []
        for i in range(parcels_per_project):
            dcfg = random.choice(matching_districts)
            village = random.choice(dcfg["villages"])
            owner = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            survey_num = f"{random.randint(1, 450)}/{random.randint(1, 12)}"

            area_ha = round(random.uniform(0.15, 6.5), 3)
            stage = random.choices(stage_choices, weights=stage_weights)[0]
            stage_idx = [s.value for s in STAGE_ORDER].index(stage)

            if stage == StageName.CLOSURE.value:
                status = ParcelStatus.COMPLETED.value
                risk_score = round(random.uniform(0.0, 15.0), 1)
            elif stage in (StageName.OBJECTION.value, StageName.REHABILITATION_RESETTLEMENT.value) and random.random() < 0.25:
                status = ParcelStatus.BLOCKED.value
                risk_score = round(random.uniform(70.0, 95.0), 1)
            else:
                status = ParcelStatus.IN_PROGRESS.value
                risk_score = round(random.uniform(10.0, 65.0), 1)

            parcel_id = deterministic_uuid("pcl", f"{proj.name}:{i}")
            geom_wkt = generate_polygon_wkt(dcfg["center_lat"], dcfg["center_lon"], i)

            parcel = Parcel(
                parcel_id=parcel_id,
                project_id=proj.project_id,
                survey_number=survey_num,
                area_ha=area_ha,
                geometry=WKTElement(geom_wkt, srid=4326),
                owner_name=owner,
                owner_reference=f"UID-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                current_stage=stage,
                status=status,
                risk_score=risk_score,
                village=village,
                district=dcfg["district"],
                state=dcfg["state"],
                assigned_officer=field_user.id if random.random() < 0.7 else None,
                created_at=now_utc - timedelta(days=random.randint(30, 300)),
            )
            p_batch.append(parcel)

            for s_order, s_enum in enumerate(STAGE_ORDER, start=1):
                s_name = s_enum.value
                if s_order <= stage_idx:
                    s_status = StageStatus.COMPLETED.value
                    s_start = today - timedelta(days=(stage_idx - s_order + 1) * 30 + 15)
                    s_target = s_start + timedelta(days=30)
                    s_comp = s_start + timedelta(days=25)
                elif s_order == stage_idx + 1:
                    s_status = StageStatus.IN_PROGRESS.value if status != ParcelStatus.BLOCKED.value else StageStatus.BLOCKED.value
                    s_start = today - timedelta(days=random.randint(5, 20))
                    s_target = today - timedelta(days=random.randint(2, 14)) if random.random() < 0.12 else today + timedelta(days=random.randint(15, 60))
                    s_comp = None
                else:
                    s_status = StageStatus.NOT_STARTED.value
                    s_start, s_target, s_comp = None, None, None

                s_batch.append(
                    AcquisitionStage(
                        stage_id=deterministic_uuid("stg", f"{parcel_id}:{s_name}"),
                        parcel_id=parcel_id,
                        stage_name=s_name,
                        stage_order=s_order,
                        start_date=s_start,
                        target_date=s_target,
                        completion_date=s_comp,
                        status=s_status,
                        assigned_officer=field_user.id,
                        remarks="Demo stage entry",
                    )
                )

            if stage_idx >= [s.value for s in STAGE_ORDER].index(StageName.AWARD.value):
                land_val = round(area_ha * random.uniform(2500000, 7500000), 2)
                solatium = round(land_val * 1.0, 2)
                total_calc = round(land_val * 1.5 + solatium, 2)
                paid_amt = total_calc if stage in (StageName.POSSESSION.value, StageName.CLOSURE.value) else 0.0

                c_batch.append(
                    Compensation(
                        compensation_id=deterministic_uuid("cmp", str(parcel_id)),
                        parcel_id=parcel_id,
                        assessed_amount=total_calc,
                        approved_amount=total_calc,
                        paid_amount=paid_amt,
                        payment_status=CompensationPaymentStatus.DISBURSED.value if paid_amt >= total_calc else CompensationPaymentStatus.APPROVED.value,
                        payment_date=today - timedelta(days=15) if paid_amt >= total_calc else None,
                        remarks="Calculated per RFCTLARR statutory rules.",
                    )
                )

        db.add_all(p_batch)
        db.add_all(s_batch)
        db.add_all(c_batch)
        db.commit()
        print(f"   [OK] Seeded {len(p_batch)} parcels for: {proj.name[:40]}...")

        # Timeline snapshots
        snap_batch = []
        for h_idx in range(6):
            h_date = (now_utc - timedelta(days=(6 - h_idx) * 15)).date()
            comp_pct = max(0.05, min(0.95, (h_idx + 1) / 7))
            snap_batch.append(
                ProjectHistory(
                    snapshot_id=deterministic_uuid("snap", f"{proj.name}:{h_idx}"),
                    project_id=proj.project_id,
                    snapshot_date=h_date,
                    land_required_ha=proj.land_required_ha,
                    land_acquired_ha=round(proj.land_required_ha * comp_pct * 0.6, 2),
                    parcels_total=parcels_per_project,
                    parcels_completed=int(parcels_per_project * comp_pct * 0.7),
                    parcels_in_progress=int(parcels_per_project * 0.4),
                    parcels_disputed=random.randint(2, 10),
                    compensation_paid_total=round(proj.land_required_ha * 2500000 * comp_pct, 2),
                    compensation_pending_total=round(proj.land_required_ha * 1000000, 2),
                    stages_snapshot={"SURVEY": 20, "AWARD": 15, "COMPENSATION": 10},
                    metadata_json={
                        "pending_parcels": 25.0,
                        "completed_parcels": 20.0,
                        "average_stage_days": 38.0,
                        "sla_breaches": 4.0,
                        "compensation_pending": 8.0,
                        "rr_pending": 5.0,
                        "possession_pending": 3.0,
                        "processing_rate": 0.18,
                        "officers_count": 4,
                    },
                )
            )
        db.add_all(snap_batch)
        db.commit()


# ── Main Entrypoint ──────────────────────────────────────────────────────────

def seed_database(source: str = "demo", reset: bool = False) -> None:
    print("=" * 70)
    print(f"  BHOOMI-SETU -- Database Seeder [Source: {source.upper()}]")
    print("=" * 70)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if reset or os.getenv("FORCE_SEED", "false").lower() in ("true", "1", "yes"):
            reset_database(db)

        # Core accounts and administrative boundaries are always guaranteed
        user_map = seed_users(db)
        seed_boundaries(db)

        # Robust path discovery for synthetic dataset
        candidate_dirs = [
            Path(parent_dir).parent / "data" / "synthetic",
            Path(parent_dir) / "data" / "synthetic",
            Path("data/synthetic").resolve(),
            Path("../data/synthetic").resolve(),
            Path("/app/data/synthetic"),
        ]
        data_synthetic_dir = next((cd for cd in candidate_dirs if cd.exists() and (cd / "projects.csv").exists()), None)

        if source in ("synthetic", "project") and data_synthetic_dir:
            seed_from_synthetic(db, user_map, data_synthetic_dir)
        else:
            seed_demo(db, user_map)

        print("\n" + "=" * 70)
        print("  [SUCCESS] DATABASE SEED COMPLETED SUCCESSFULLY!")
        print("  - Demo credentials: admin / central_user / state_user / district_user")
        print("  - Default password: password123")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed with error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BhoomiSetu Database Seeder")
    parser.add_argument(
        "--source",
        choices=["demo", "synthetic", "project"],
        default=settings.data_source if settings.data_source in ("synthetic", "project") else "demo",
        help="Data source mode: 'synthetic' loads from data/synthetic CSVs, 'demo' runs procedural generator.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe all existing database records before seeding.",
    )
    args = parser.parse_args()
    seed_database(source=args.source, reset=args.reset)

"""Synthetic data loader — populates the database with demo users, projects, parcels, stages, and boundaries."""

from __future__ import annotations

import os
import sys
import uuid
import random
from datetime import date, datetime, timedelta, timezone

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from sqlalchemy import select, text
from geoalchemy2.elements import WKTElement

from app.database import engine, SessionLocal, Base
from app.core.security import hash_password
from app.models import (
    User,
    Project,
    Parcel,
    AcquisitionStage,
    Compensation,
    RRRecord,
    AuditLog,
    GISBoundary,
    ProjectHistory,
)
from app.models.enums import (
    UserRole,
    ProjectStatus,
    StageName,
    ParcelStatus,
    StageStatus,
    CompensationPaymentStatus,
    AffectedType,
    RehabilitationStatus,
)
from app.services.transition import STAGE_ORDER


# ── Location Configurations ───────────────────────────────────────────────────

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
]

FIRST_NAMES = [
    "Ramesh", "Suresh", "Rajesh", "Sunita", "Ananya", "Mohanlal", "Ganesh", "Pooja",
    "Vikram", "Deepak", "Kavita", "Sanjay", "Santosh", "Prakash", "Amit", "Rahul",
    "Priyanka", "Nitin", "Mahesh", "Kishore", "Vijay", "Balasaheb", "Chandrakant",
    "Jyoti", "Laxman", "Subhash", "Manish", "Dattatray", "Ashok", "Pandurang"
]

LAST_NAMES = [
    "Patil", "Deshmukh", "Sharma", "Gaikwad", "Gupta", "Joshi", "Shinde", "Pawar",
    "Chavan", "Kulkarni", "Jadhav", "More", "Bhosale", "Shekhawat", "Choudhary",
    "Rathore", "Bishnoi", "Meena", "Tambe", "Kadam", "Sawant", "Ghate", "Mane", "Wagh"
]


def generate_polygon_wkt(center_lat: float, center_lon: float, offset_idx: int) -> str:
    """Generate a small realistic polygon near the center point."""
    # Jitter base
    lat_offset = ((offset_idx % 40) - 20) * 0.003 + random.uniform(-0.001, 0.001)
    lon_offset = ((offset_idx // 40) - 20) * 0.003 + random.uniform(-0.001, 0.001)

    lat = center_lat + lat_offset
    lon = center_lon + lon_offset

    d = random.uniform(0.0008, 0.0025)
    # 4-corner polygon closed
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


def seed_database():
    print("=" * 70)
    print("  BHOOMI-SETU -- Database Seeder (Phases 1-3)")
    print("=" * 70)

    # Ensure tables exist
    print("\n1. Ensuring database tables are created...")
    Base.metadata.create_all(bind=engine)
    print("   [OK] Base schema tables ready.")

    db = SessionLocal()

    try:
        # Check if already seeded
        existing_user_count = db.execute(select(User)).scalars().all()
        if len(existing_user_count) >= 6:
            print(f"   [INFO] Found {len(existing_user_count)} existing users. Database already initialized.")
            user_confirm = os.getenv("FORCE_SEED", "false").lower() in ("true", "1", "yes")
            if not user_confirm:
                print("   [INFO] To re-seed from scratch, set FORCE_SEED=true. Exiting gracefully.")
                return

        # ── 2. Seed Users ─────────────────────────────────────────────────────
        print("\n2. Seeding 6 demo user accounts (one per role)...")
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
                "email": "state.mh@bhoomisetu.gov.in",
                "role": UserRole.STATE.value,
                "state_scope": "Maharashtra",
                "district_scope": None,
            },
            {
                "username": "district_user",
                "email": "collector.pune@bhoomisetu.gov.in",
                "role": UserRole.DISTRICT.value,
                "state_scope": "Maharashtra",
                "district_scope": "Pune",
            },
            {
                "username": "agency_user",
                "email": "nhai.agency@bhoomisetu.gov.in",
                "role": UserRole.PROJECT_AGENCY.value,
                "state_scope": "Maharashtra",
                "district_scope": "Pune",
            },
            {
                "username": "field_officer",
                "email": "officer.haveli@bhoomisetu.gov.in",
                "role": UserRole.FIELD_OFFICER.value,
                "state_scope": "Maharashtra",
                "district_scope": "Pune",
            },
        ]

        user_map: dict[str, User] = {}
        for udata in demo_users_data:
            existing = db.execute(select(User).where(User.username == udata["username"])).scalar_one_or_none()
            if not existing:
                u = User(
                    id=uuid.uuid4(),
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

        admin_user = user_map["admin"]
        field_officer_user = user_map["field_officer"]

        # ── 3. Seed GIS Boundaries ────────────────────────────────────────────
        print("\n3. Seeding administrative boundaries (States & Districts)...")
        boundary_entries = [
            # States
            {"level": "state", "name": "Maharashtra", "parent": "India", "state": "Maharashtra", "dist": None, "lat": 19.7515, "lon": 75.7139, "size": 1.5},
            {"level": "state", "name": "Rajasthan", "parent": "India", "state": "Rajasthan", "dist": None, "lat": 27.0238, "lon": 74.2179, "size": 1.5},
            {"level": "state", "name": "Gujarat", "parent": "India", "state": "Gujarat", "dist": None, "lat": 22.2587, "lon": 71.1924, "size": 1.2},
            # Districts
            {"level": "district", "name": "Pune", "parent": "Maharashtra", "state": "Maharashtra", "dist": "Pune", "lat": 18.5204, "lon": 73.8567, "size": 0.4},
            {"level": "district", "name": "Thane", "parent": "Maharashtra", "state": "Maharashtra", "dist": "Thane", "lat": 19.2183, "lon": 72.9781, "size": 0.3},
            {"level": "district", "name": "Raigad", "parent": "Maharashtra", "state": "Maharashtra", "dist": "Raigad", "lat": 18.5158, "lon": 73.1822, "size": 0.35},
            {"level": "district", "name": "Palghar", "parent": "Maharashtra", "state": "Maharashtra", "dist": "Palghar", "lat": 19.6967, "lon": 72.7699, "size": 0.35},
            {"level": "district", "name": "Jaipur", "parent": "Rajasthan", "state": "Rajasthan", "dist": "Jaipur", "lat": 26.9124, "lon": 75.7873, "size": 0.4},
            {"level": "district", "name": "Jodhpur", "parent": "Rajasthan", "state": "Rajasthan", "dist": "Jodhpur", "lat": 26.2389, "lon": 73.0243, "size": 0.45},
        ]

        # Add sample village boundaries
        for dcfg in DISTRICT_CONFIGS:
            for vname in dcfg["villages"][:3]:
                boundary_entries.append({
                    "level": "village",
                    "name": vname,
                    "parent": dcfg["district"],
                    "state": dcfg["state"],
                    "dist": dcfg["district"],
                    "lat": dcfg["center_lat"] + random.uniform(-0.05, 0.05),
                    "lon": dcfg["center_lon"] + random.uniform(-0.05, 0.05),
                    "size": 0.05,
                })

        for b in boundary_entries:
            geom_wkt = generate_multipolygon_wkt(b["lat"], b["lon"], b["size"])
            boundary = GISBoundary(
                boundary_id=uuid.uuid4(),
                level=b["level"],
                name=b["name"],
                parent_name=b["parent"],
                state_name=b["state"],
                district_name=b["dist"],
                geometry=WKTElement(geom_wkt, srid=4326),
            )
            db.add(boundary)
        db.commit()
        print(f"   [OK] Seeded {len(boundary_entries)} boundary polygons (State, District, Village).")

        # ── 4. Seed Infrastructure Projects ───────────────────────────────────
        print("\n4. Seeding infrastructure projects...")
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
                    project_id=uuid.uuid4(),
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

        # ── 5. Seed 2,200+ Synthetic Parcels ──────────────────────────────────
        print("\n5. Generating and seeding 2,200+ synthetic parcels with stages & compensation...")

        # Target: ~370 parcels per project = 2,220 parcels
        parcels_per_project = 370
        total_parcels_seeded = 0

        # Stage distribution weighting (realistic lifecycle spread)
        stage_choices = [s.value for s in STAGE_ORDER]
        stage_weights = [0.08, 0.10, 0.12, 0.12, 0.14, 0.10, 0.10, 0.08, 0.06, 0.06, 0.04]

        # Map district configs for easy lookup
        district_lookup = {d["district"]: d for d in DISTRICT_CONFIGS}

        now_utc = datetime.now(timezone.utc)
        today = now_utc.date()

        for proj in created_projects:
            # Find eligible district configs for this project
            matching_districts = [
                d for d in DISTRICT_CONFIGS
                if d["district"] in proj.districts or d["state"] in proj.states
            ]
            if not matching_districts:
                matching_districts = DISTRICT_CONFIGS[:2]

            parcels_batch = []
            stages_batch = []
            comp_batch = []
            rr_batch = []

            for i in range(parcels_per_project):
                dcfg = random.choice(matching_districts)
                village = random.choice(dcfg["villages"])
                owner = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
                survey_num = f"{random.randint(1, 450)}/{random.randint(1, 12)}"
                if random.random() < 0.3:
                    survey_num += f"-{random.choice(['A', 'B', 'C', 'D'])}"

                area_ha = round(random.uniform(0.15, 6.5), 3)

                # Pick stage
                stage = random.choices(stage_choices, weights=stage_weights)[0]
                stage_idx = [s.value for s in STAGE_ORDER].index(stage)

                # Determine parcel status based on stage
                if stage == StageName.CLOSURE.value:
                    status = ParcelStatus.COMPLETED.value
                    risk_score = round(random.uniform(0.0, 15.0), 1)
                elif stage == StageName.PROPOSAL.value:
                    status = ParcelStatus.NOT_STARTED.value
                    risk_score = round(random.uniform(5.0, 30.0), 1)
                elif stage in (StageName.OBJECTION.value, StageName.REHABILITATION_RESETTLEMENT.value) and random.random() < 0.25:
                    status = ParcelStatus.BLOCKED.value
                    risk_score = round(random.uniform(70.0, 95.0), 1)
                elif random.random() < 0.08:
                    status = ParcelStatus.DISPUTED.value
                    risk_score = round(random.uniform(75.0, 99.0), 1)
                else:
                    status = ParcelStatus.IN_PROGRESS.value
                    risk_score = round(random.uniform(10.0, 65.0), 1)

                parcel_id = uuid.uuid4()
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
                    assigned_officer=field_officer_user.id if random.random() < 0.7 else None,
                    created_at=now_utc - timedelta(days=random.randint(30, 300)),
                )
                parcels_batch.append(parcel)

                # Build AcquisitionStage history up to the current stage
                for s_order, s_enum in enumerate(STAGE_ORDER, start=1):
                    s_name = s_enum.value
                    if s_order <= stage_idx:
                        # Completed past stage
                        s_status = StageStatus.COMPLETED.value
                        s_start = today - timedelta(days=(stage_idx - s_order + 1) * 30 + 15)
                        s_target = s_start + timedelta(days=30)
                        s_comp = s_start + timedelta(days=25)
                    elif s_order == stage_idx + 1:
                        # Current active stage
                        s_status = StageStatus.IN_PROGRESS.value if status != ParcelStatus.BLOCKED.value else StageStatus.BLOCKED.value
                        s_start = today - timedelta(days=random.randint(5, 20))
                        # Intentionally make ~10% have target_date in the past (SLA breach demo)
                        if random.random() < 0.12:
                            s_target = today - timedelta(days=random.randint(2, 14))
                        else:
                            s_target = today + timedelta(days=random.randint(15, 60))
                        s_comp = None
                    else:
                        # Future stage
                        s_status = StageStatus.NOT_STARTED.value
                        s_start = None
                        s_target = None
                        s_comp = None

                    stage_entry = AcquisitionStage(
                        stage_id=uuid.uuid4(),
                        parcel_id=parcel_id,
                        stage_name=s_name,
                        stage_order=s_order,
                        start_date=s_start,
                        target_date=s_target,
                        completion_date=s_comp,
                        status=s_status,
                        assigned_officer=field_officer_user.id,
                        remarks="Auto-generated stage" if s_order == stage_idx + 1 else None,
                    )
                    stages_batch.append(stage_entry)

                # Compensation record for parcels that reached AWARD stage or beyond
                if stage_idx >= [s.value for s in STAGE_ORDER].index(StageName.AWARD.value):
                    land_val = round(area_ha * random.uniform(2500000, 7500000), 2)
                    solatium = round(land_val * 1.0, 2)  # 100% solatium per RFCTLARR Act
                    multiplier = 1.5 if dcfg["state"] == "Maharashtra" else 1.25
                    total_calc = round((land_val * multiplier) + solatium, 2)
                    paid_amt = total_calc if stage in (StageName.POSSESSION.value, StageName.CLOSURE.value) else (total_calc * 0.5 if stage == StageName.COMPENSATION.value else 0.0)

                    pay_status = (
                        CompensationPaymentStatus.DISBURSED.value
                        if paid_amt >= total_calc
                        else (CompensationPaymentStatus.PARTIALLY_PAID.value if paid_amt > 0 else CompensationPaymentStatus.APPROVED.value)
                    )

                    comp = Compensation(
                        compensation_id=uuid.uuid4(),
                        parcel_id=parcel_id,
                        assessed_amount=total_calc,
                        approved_amount=total_calc,
                        paid_amount=paid_amt,
                        payment_status=pay_status,
                        payment_date=today - timedelta(days=15) if pay_status == CompensationPaymentStatus.DISBURSED.value else None,
                        remarks="Calculated per RFCTLARR statutory rules.",
                    )
                    comp_batch.append(comp)

                # R&R Record for parcels in R&R stage or beyond
                if stage_idx >= [s.value for s in STAGE_ORDER].index(StageName.REHABILITATION_RESETTLEMENT.value):
                    rr = RRRecord(
                        rr_id=uuid.uuid4(),
                        parcel_id=parcel_id,
                        paf_name=owner,
                        paf_type=random.choice([AffectedType.TITLE_HOLDER.value, AffectedType.TENANT.value, AffectedType.AGRICULTURAL_LABOURER.value]),
                        family_size=random.randint(2, 7),
                        affected_area_ha=round(area_ha * 0.8, 3),
                        rehabilitation_status=RehabilitationStatus.COMPLETED.value if stage == StageName.CLOSURE.value else RehabilitationStatus.PLAN_APPROVED.value,
                        compensation_paid=50000.0,
                        relocation_site=f"{village} New Resettlement Colony",
                        plot_allotted=f"Plot-{random.randint(101, 999)}",
                    )
                    rr_batch.append(rr)

            # Insert batch
            db.add_all(parcels_batch)
            db.add_all(stages_batch)
            db.add_all(comp_batch)
            db.add_all(rr_batch)
            db.commit()

            total_parcels_seeded += len(parcels_batch)
            print(f"   [OK] Seeded {len(parcels_batch)} parcels for project: {proj.name[:45]}...")

            # Seed 5-8 historical timeline snapshots for this project
            n_history = random.randint(5, 8)
            snap_batch = []
            for h_idx in range(n_history):
                h_date = (now_utc - timedelta(days=(n_history - h_idx) * 15)).date()
                comp_pct = max(0.05, min(0.95, (h_idx + 1) / (n_history + 1)))
                c_done = int(parcels_per_project * comp_pct * 0.7)
                c_prog = int(parcels_per_project * 0.4)
                c_block = random.randint(2, 10)
                snap_batch.append(
                    ProjectHistory(
                        snapshot_id=uuid.uuid4(),
                        project_id=proj.project_id,
                        snapshot_date=h_date,
                        land_required_ha=proj.land_required_ha,
                        land_acquired_ha=round(proj.land_required_ha * comp_pct * 0.6, 2),
                        parcels_total=parcels_per_project,
                        parcels_completed=c_done,
                        parcels_in_progress=c_prog,
                        parcels_disputed=c_block,
                        compensation_paid_total=round(proj.land_required_ha * 2500000 * comp_pct, 2),
                        compensation_pending_total=round(proj.land_required_ha * 1000000, 2),
                        stages_snapshot={
                            "SURVEY": int(c_prog * 0.3),
                            "VERIFICATION": int(c_prog * 0.3),
                            "OBJECTION": int(c_block * 0.6),
                            "AWARD": int(c_prog * 0.2),
                            "COMPENSATION": int(c_prog * 0.2),
                        },
                        metadata_json={
                            "officers_count": 4,
                            "sla_breaches": random.randint(1, 6),
                            "disputes_count": random.randint(1, 5),
                            "avg_days_per_stage": round(random.uniform(25.0, 55.0), 1),
                            "stage_complexity": round(random.uniform(0.4, 0.75), 4),
                        },
                    )
                )
            db.add_all(snap_batch)
            db.commit()

        # ── 6. Seed Sample Audit Log Entries ──────────────────────────────────
        print("\n6. Seeding initial audit ledger entries...")
        sample_audit_logs = []
        for i in range(15):
            sample_audit_logs.append(
                AuditLog(
                    log_id=uuid.uuid4(),
                    user_id=field_officer_user.id,
                    action="STAGE_TRANSITION",
                    entity_type="parcel",
                    entity_id=uuid.uuid4(),
                    old_values={"stage": StageName.SURVEY.value},
                    new_values={"stage": StageName.VERIFICATION.value, "remarks": f"Joint measurement survey completed for block #{i+1}"},
                    ip_address="127.0.0.1",
                    user_agent="BhoomiSetu-Client/1.0",
                    created_at=now_utc - timedelta(hours=random.randint(1, 72)),
                )
            )
        db.add_all(sample_audit_logs)
        db.commit()
        print(f"   [OK] Seeded {len(sample_audit_logs)} audit log records.")

        print("\n" + "=" * 70)
        print(f"  [SUCCESS] SEED COMPLETED SUCCESSFULLY!")
        print(f"  - Users:       6 demo accounts (admin, central, state, district, agency, field)")
        print(f"  - Password:    {password_plain}")
        print(f"  - Projects:    {len(created_projects)} infrastructure corridors")
        print(f"  - Parcels:     {total_parcels_seeded} synthetic parcels with stages")
        print(f"  - Boundaries:  {len(boundary_entries)} administrative polygons")
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
    seed_database()

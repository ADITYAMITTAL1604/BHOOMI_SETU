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
    Alert,
    AuditLog,
    Compensation,
    GISBoundary,
    Parcel,
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
    # ── Uttar Pradesh (Delhi-NCR Corridor) ──
    {
        "state": "Uttar Pradesh",
        "district": "Ghaziabad",
        "center_lat": 28.6692,
        "center_lon": 77.4538,
        "villages": ["Sahibabad", "Guldhar", "Duhai", "Muradnagar", "Modinagar", "Morti", "Bhudbaral", "Morta"],
    },
    {
        "state": "Uttar Pradesh",
        "district": "Meerut",
        "center_lat": 28.9845,
        "center_lon": 77.7064,
        "villages": ["Partapur", "Rithani", "Shatabdi Nagar", "Brahampuri", "Begumpul", "Modipuram", "Mohiuddinpur", "Daurala"],
    },
    # ── Delhi (NCT Urban & Transit Corridors) ──
    {
        "state": "Delhi",
        "district": "East Delhi",
        "center_lat": 28.6280,
        "center_lon": 77.2951,
        "villages": ["Sarai Kale Khan", "Shakarpur", "Mandawali", "Patparganj", "Ghazipur", "Kalyanpuri", "Khichripur"],
    },
    {
        "state": "Delhi",
        "district": "South Delhi",
        "center_lat": 28.5244,
        "center_lon": 77.2000,
        "villages": ["Saket", "Neb Sarai", "Khanpur", "Sangam Vihar", "Tughlakabad", "Chhatarpur", "Maidan Garhi", "Lado Sarai"],
    },
    {
        "state": "Delhi",
        "district": "South West Delhi",
        "center_lat": 28.5824,
        "center_lon": 77.0550,
        "villages": ["Aerocity", "Mahipalpur", "Vasant Kunj", "Kapashera", "Bijwasan", "Samalkha", "Dwarka Sector 21"],
    },
    # ── Maharashtra (Samruddhi, Ring Road, MAHSR, JNPT Corridors) ──
    {
        "state": "Maharashtra",
        "district": "Thane",
        "center_lat": 19.2183,
        "center_lon": 73.0500,
        "villages": ["Bhiwandi", "Amane", "Shahapur", "Diva", "Shilphata", "Padgha", "Vashind", "Asangaon"],
    },
    {
        "state": "Maharashtra",
        "district": "Palghar",
        "center_lat": 19.7500,
        "center_lon": 72.8500,
        "villages": ["Boisar", "Dahanu", "Talasari", "Manor", "Wada", "Kelve", "Saphale", "Vikramgad"],
    },
    {
        "state": "Maharashtra",
        "district": "Raigad",
        "center_lat": 18.8500,
        "center_lon": 73.0500,
        "villages": ["Nhava Sheva", "Jasai", "Dronagiri", "Chirle", "Panvel", "Ulwe", "Karanjade", "Dapoli"],
    },
    {
        "state": "Maharashtra",
        "district": "Pune",
        "center_lat": 18.5204,
        "center_lon": 73.8567,
        "villages": ["Wagholi", "Hinjawadi", "Maan", "Chakan", "Pirangut", "Urse", "Lonikand", "Parandwadi"],
    },
    {
        "state": "Maharashtra",
        "district": "Nagpur",
        "center_lat": 21.1458,
        "center_lon": 79.0882,
        "villages": ["Shivmadka", "Butibori", "Wadi", "Hingna", "Gumgaon", "Asoli", "Bhilgaon"],
    },
    {
        "state": "Maharashtra",
        "district": "Nashik",
        "center_lat": 19.9975,
        "center_lon": 73.7898,
        "villages": ["Sinnar", "Igatpuri", "Ghoti", "Panchale", "Dodi", "Musgaon", "Vinchur"],
    },
    # ── Punjab (Amritsar-Jamnagar & Freight Corridors) ──
    {
        "state": "Punjab",
        "district": "Amritsar",
        "center_lat": 31.6340,
        "center_lon": 74.8723,
        "villages": ["Tibba", "Chheharta", "Verka", "Manawala", "Jandiala Guru", "Attari", "Khasa"],
    },
    {
        "state": "Punjab",
        "district": "Tarn Taran",
        "center_lat": 31.4520,
        "center_lon": 74.9254,
        "villages": ["Patti", "Naushehra", "Harike", "Goindwal Sahib", "Chabal", "Bhikhiwind"],
    },
    {
        "state": "Punjab",
        "district": "Moga",
        "center_lat": 30.8165,
        "center_lon": 75.1717,
        "villages": ["Baghapurana", "Dharamkot", "Kotkapura Road", "Badhni Kalan", "Singhanwala"],
    },
    {
        "state": "Punjab",
        "district": "Bathinda",
        "center_lat": 30.2110,
        "center_lon": 74.9455,
        "villages": ["Rampura Phul", "Sangat", "Goniana", "Bhucho Mandi", "Maur", "Kot Shamir"],
    },
    {
        "state": "Punjab",
        "district": "Ludhiana",
        "center_lat": 30.9010,
        "center_lon": 75.8573,
        "villages": ["Sahnewal", "Doraha", "Khanna", "Mullanpur", "Dehlon", "Kohara"],
    },
    {
        "state": "Punjab",
        "district": "Patiala",
        "center_lat": 30.3398,
        "center_lon": 76.3869,
        "villages": ["Rajpura", "Shambhu", "Ghanaur", "Banur", "Sanaur", "Khaspur"],
    },
    # ── Rajasthan (WDFC, Ring Road, Refinery Corridors) ──
    {
        "state": "Rajasthan",
        "district": "Jaipur",
        "center_lat": 26.9124,
        "center_lon": 75.7873,
        "villages": ["Bagru", "Shivdaspura", "Vatika", "Bassi", "Chaksu", "Phulera", "Asalpur", "Kotputli"],
    },
    {
        "state": "Rajasthan",
        "district": "Jodhpur",
        "center_lat": 26.2389,
        "center_lon": 73.0243,
        "villages": ["Luni", "Borunda", "Pipar", "Salawas", "Mogra", "Jhalamand"],
    },
    {
        "state": "Rajasthan",
        "district": "Balotra",
        "center_lat": 25.8344,
        "center_lon": 72.2415,
        "villages": ["Pachpadra", "Sambhra", "Asotra", "Mandawala", "Kalyanpur", "Jasol", "Bithuja"],
    },
    {
        "state": "Rajasthan",
        "district": "Barmer",
        "center_lat": 25.7521,
        "center_lon": 71.3967,
        "villages": ["Baytu", "Nagana", "Kawas", "Sindhari", "Jasai", "Guda"],
    },
    {
        "state": "Rajasthan",
        "district": "Ajmer",
        "center_lat": 26.4499,
        "center_lon": 74.6399,
        "villages": ["Kishangarh", "Madanganj", "Gegal", "Gugra", "Tabiji", "Mangliyawas"],
    },
    {
        "state": "Rajasthan",
        "district": "Pali",
        "center_lat": 25.7711,
        "center_lon": 73.3234,
        "villages": ["Marwar Junction", "Rohat", "Sojat Road", "Gundoj", "Rani", "Falna"],
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


import math

def generate_linestring_wkt(waypoints: list[tuple[float, float]]) -> str:
    """Generate PostGIS LINESTRING from waypoints (lat, lon)."""
    coords = [f"{lon:.6f} {lat:.6f}" for lat, lon in waypoints]
    return f"LINESTRING({', '.join(coords)})"


def interpolate_corridor(waypoints: list[tuple[float, float]], u: float):
    """
    Interpolate position and tangent along waypoints at fraction u (0.0 <= u <= 1.0).
    Returns (lat, lon, tx, ty, nx, ny).
    """
    if len(waypoints) < 2:
        lat, lon = waypoints[0]
        return lat, lon, 1.0, 0.0, 0.0, 1.0

    seg_lens = []
    for j in range(len(waypoints) - 1):
        lat1, lon1 = waypoints[j]
        lat2, lon2 = waypoints[j + 1]
        sl = math.hypot(lon2 - lon1, lat2 - lat1)
        seg_lens.append(max(sl, 1e-6))

    total_len = sum(seg_lens)
    target_d = max(0.0, min(1.0, u)) * total_len

    cum_d = 0.0
    for j, sl in enumerate(seg_lens):
        if cum_d + sl >= target_d or j == len(seg_lens) - 1:
            local_u = (target_d - cum_d) / sl
            local_u = max(0.0, min(1.0, local_u))
            lat1, lon1 = waypoints[j]
            lat2, lon2 = waypoints[j + 1]
            lat_c = lat1 + local_u * (lat2 - lat1)
            lon_c = lon1 + local_u * (lon2 - lon1)

            dx = lon2 - lon1
            dy = lat2 - lat1
            mag = math.hypot(dx, dy)
            if mag == 0:
                mag = 1e-6
            tx = dx / mag
            ty = dy / mag
            nx = -ty
            ny = tx
            return lat_c, lon_c, tx, ty, nx, ny
        cum_d += sl

    lat_last, lon_last = waypoints[-1]
    return lat_last, lon_last, 1.0, 0.0, 0.0, 1.0


def generate_linear_cadastral_polygon_wkt(waypoints: list[tuple[float, float]], fraction: float, idx: int) -> str:
    """
    Generate an authentic cadastral survey parcel polygon along the corridor right-of-way.
    Alternates left and right sides of the corridor centerline with distinct surveyed boundaries.
    """
    lat_c, lon_c, tx, ty, nx, ny = interpolate_corridor(waypoints, fraction)

    # Alternate side (left = 1, right = -1)
    side = 1 if (idx % 2 == 0) else -1

    # Width offset from centerline (approx 30m to 120m in degrees, where 0.001 deg approx 110m)
    w_inner = side * (0.00020 + random.uniform(0.0, 0.00010))
    w_outer = side * (abs(w_inner) + 0.00070 + random.uniform(0.0, 0.00035))

    # Length along corridor tangent (approx 70m to 140m)
    half_len = 0.00050 + random.uniform(0.0, 0.00020)

    # 4 polygon corners
    p1_lon = lon_c - half_len * tx + w_inner * nx
    p1_lat = lat_c - half_len * ty + w_inner * ny

    p2_lon = lon_c + half_len * tx + w_inner * nx
    p2_lat = lat_c + half_len * ty + w_inner * ny

    p3_lon = lon_c + half_len * tx + w_outer * nx
    p3_lat = lat_c + half_len * ty + w_outer * ny

    p4_lon = lon_c - half_len * tx + w_outer * nx
    p4_lat = lat_c - half_len * ty + w_outer * ny

    if side < 0:
        pts = [(p1_lon, p1_lat), (p4_lon, p4_lat), (p3_lon, p3_lat), (p2_lon, p2_lat), (p1_lon, p1_lat)]
    else:
        pts = [(p1_lon, p1_lat), (p2_lon, p2_lat), (p3_lon, p3_lat), (p4_lon, p4_lat), (p1_lon, p1_lat)]

    ring_str = ", ".join([f"{lon:.6f} {lat:.6f}" for lon, lat in pts])
    return f"POLYGON(({ring_str}))"


def generate_polygon_wkt(center_lat: float, center_lon: float, offset_idx: int) -> str:
    """Generate a small realistic polygon near the center point (fallback)."""
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
    """Generate a LineString corridor geometry from two points."""
    mid_lat = (lat1 + lat2) / 2 + random.uniform(-0.02, 0.02)
    mid_lon = (lon1 + lon2) / 2 + random.uniform(-0.02, 0.02)
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
    db_url = str(engine.url)
    if "supabase" in db_url.lower() and os.getenv("ALLOW_PROD_RESET", "false").lower() not in ("true", "1", "yes"):
        print("   [RESET BLOCKED] Refusing to wipe production/cloud Supabase database without ALLOW_PROD_RESET=true!")
        return

    print("   [RESET] Truncating existing tables...")
    tables = [
        "document_approvals",
        "notifications",
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
        {
            "username": "delhi_state",
            "email": "state.delhi@bhoomisetu.gov.in",
            "role": UserRole.STATE.value,
            "state_scope": "Delhi",
            "district_scope": None,
        },
        {
            "username": "delhi_district",
            "email": "collector.southdelhi@bhoomisetu.gov.in",
            "role": UserRole.DISTRICT.value,
            "state_scope": "Delhi",
            "district_scope": "South Delhi",
        },
        {
            "username": "punjab_state",
            "email": "state.punjab@bhoomisetu.gov.in",
            "role": UserRole.STATE.value,
            "state_scope": "Punjab",
            "district_scope": None,
        },
        {
            "username": "punjab_district",
            "email": "collector.amritsar@bhoomisetu.gov.in",
            "role": UserRole.DISTRICT.value,
            "state_scope": "Punjab",
            "district_scope": "Amritsar",
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
    state_entries = [
        {"level": "state", "name": "Maharashtra", "parent": "India", "state": "Maharashtra", "dist": None, "lat": 19.7515, "lon": 75.7139, "size": 1.5},
        {"level": "state", "name": "Rajasthan", "parent": "India", "state": "Rajasthan", "dist": None, "lat": 27.0238, "lon": 74.2179, "size": 1.5},
        {"level": "state", "name": "Uttar Pradesh", "parent": "India", "state": "Uttar Pradesh", "dist": None, "lat": 26.8467, "lon": 80.9462, "size": 1.6},
        {"level": "state", "name": "Gujarat", "parent": "India", "state": "Gujarat", "dist": None, "lat": 22.2587, "lon": 71.1924, "size": 1.2},
        {"level": "state", "name": "Delhi", "parent": "India", "state": "Delhi", "dist": None, "lat": 28.6139, "lon": 77.2090, "size": 0.3},
        {"level": "state", "name": "Punjab", "parent": "India", "state": "Punjab", "dist": None, "lat": 31.1471, "lon": 75.3412, "size": 1.2},
    ]

    boundary_entries = list(state_entries)

    # Automatically add district boundaries for each district in DISTRICT_CONFIGS
    for dcfg in DISTRICT_CONFIGS:
        boundary_entries.append({
            "level": "district",
            "name": dcfg["district"],
            "parent": dcfg["state"],
            "state": dcfg["state"],
            "dist": dcfg["district"],
            "lat": dcfg["center_lat"],
            "lon": dcfg["center_lon"],
            "size": 0.25 if dcfg["state"] != "Delhi" else 0.10,
        })

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

    existing_ids = set(db.execute(select(GISBoundary.boundary_id)).scalars().all())
    added = 0
    for b in boundary_entries:
        b_id = deterministic_uuid("bnd", f"{b['level']}:{b['name']}")
        if b_id not in existing_ids:
            geom_wkt = generate_multipolygon_wkt(b["lat"], b["lon"], b["size"])
            boundary = GISBoundary(
                boundary_id=b_id,
                level=b["level"],
                name=b["name"],
                parent_name=b["parent"],
                state_name=b["state"],
                district_name=b["dist"],
                geometry=WKTElement(geom_wkt, srid=4326),
            )
            db.add(boundary)
            existing_ids.add(b_id)
            added += 1
    if added > 0:
        db.commit()
        print(f"   [OK] Seeded {added} new administrative boundaries.")
    else:
        print(f"   [INFO] All {len(boundary_entries)} boundaries already present.")


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

# ── Procedural Demo Seeder (12 Audited Ground-Truth Corridors) ─────────────────

PROJECTS_AUDIT_DATA = [
    {
        "name": "Delhi-Meerut RRTS Corridor",
        "type": "Railway",
        "agency": "National Capital Region Transport Corporation",
        "states": ["Delhi", "Uttar Pradesh"],
        "districts": ["East Delhi", "Ghaziabad", "Meerut"],
        "land_required_ha": 120.0,
        "land_acquired_ha": 98.4,
        "target_date": date(2026, 12, 31),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (28.5916, 77.2575),  # Sarai Kale Khan (East Delhi)
            (28.6350, 77.3150),  # Anand Vihar
            (28.6710, 77.3600),  # Sahibabad (Ghaziabad)
            (28.6750, 77.4350),  # Ghaziabad Central
            (28.7050, 77.4700),  # Guldhar
            (28.7400, 77.4950),  # Duhai Depot
            (28.7850, 77.5100),  # Muradnagar
            (28.8400, 77.5800),  # Modinagar
            (28.9100, 77.6500),  # Partapur (Meerut)
            (28.9600, 77.6900),  # Shatabdi Nagar
            (29.0000, 77.7100),  # Begumpul
            (29.0700, 77.7150),  # Modipuram (Meerut North)
        ],
    },
    {
        "name": "Delhi-Mumbai Expressway (Vadodara-Mumbai Section)",
        "type": "Highway",
        "agency": "National Highways Authority of India",
        "states": ["Maharashtra", "Gujarat"],
        "districts": ["Palghar", "Thane", "Raigad"],
        "land_required_ha": 850.0,
        "land_acquired_ha": 540.2,
        "target_date": date(2027, 3, 31),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (20.2500, 72.9300),  # Talasari (Palghar)
            (20.0500, 72.9100),  # Dahanu
            (19.8000, 72.9500),  # Manor
            (19.6500, 73.1300),  # Wada
            (19.4500, 73.1800),  # Shahapur
            (19.3200, 73.1200),  # Amane / Bhiwandi
            (19.1000, 73.0800),  # Shilphata (Thane)
            (18.9800, 73.0700),  # Panvel / JNPT (Raigad)
        ],
    },
    {
        "name": "Pune Ring Road (Eastern & Western Alignment)",
        "type": "Highway",
        "agency": "Maharashtra State Road Development Corporation",
        "states": ["Maharashtra"],
        "districts": ["Pune"],
        "land_required_ha": 620.0,
        "land_acquired_ha": 285.0,
        "target_date": date(2026, 12, 31),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (18.6900, 73.6800),  # Urse / Parandwadi (Maval)
            (18.5900, 73.7200),  # Hinjawadi / Maan
            (18.5100, 73.7600),  # Pirangut (Mulshi)
            (18.3800, 73.8400),  # Khadakwasla / Shivane
            (18.3500, 73.9500),  # Saswad Road (Purandar)
            (18.4700, 74.0200),  # Loni Kalbhor
            (18.5800, 74.0100),  # Wagholi / Lonikand
            (18.7100, 73.9100),  # Alandi / Chakan (Khed)
        ],
    },
    {
        "name": "Mumbai-Ahmedabad High Speed Rail (MAHSR Bullet Train)",
        "type": "Railway",
        "agency": "National High Speed Rail Corporation Limited",
        "states": ["Maharashtra", "Gujarat"],
        "districts": ["Thane", "Palghar"],
        "land_required_ha": 430.0,
        "land_acquired_ha": 402.0,
        "target_date": date(2026, 8, 15),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (19.0650, 72.8680),  # BKC Mumbai Terminal
            (19.1600, 73.0100),  # Shilphata / Thane
            (19.4300, 72.8600),  # Virar
            (19.8000, 72.7600),  # Boisar (Palghar)
            (20.0500, 72.8200),  # Dahanu
            (20.2800, 72.8800),  # Talasari (Palghar border)
            (20.4000, 72.9200),  # Vapi
            (21.1800, 72.8300),  # Surat
        ],
    },
    {
        "name": "Western Dedicated Freight Corridor (WDFC - Phase 2)",
        "type": "Railway",
        "agency": "Dedicated Freight Corridor Corporation of India",
        "states": ["Rajasthan", "Maharashtra"],
        "districts": ["Jaipur", "Ajmer", "Pali", "Thane"],
        "land_required_ha": 750.0,
        "land_acquired_ha": 435.0,
        "target_date": date(2027, 6, 30),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (26.8700, 75.2400),  # Phulera Junction (Jaipur)
            (26.6800, 74.9200),  # Kishangarh
            (26.4500, 74.6400),  # Ajmer Madanganj
            (26.1500, 74.2000),  # Beawar
            (25.7700, 73.5500),  # Marwar Junction (Pali)
            (25.6000, 73.3000),  # Sojat Road
            (25.2000, 72.9500),  # Sirohi / Abu Road
        ],
    },
    {
        "name": "Jaipur Ring Road & Multimodal Logistics Hub",
        "type": "Industrial",
        "agency": "National Highways Authority of India / JDA",
        "states": ["Rajasthan"],
        "districts": ["Jaipur"],
        "land_required_ha": 380.0,
        "land_acquired_ha": 110.0,
        "target_date": date(2028, 1, 31),
        "status": ProjectStatus.PLANNING.value,
        "waypoints": [
            (26.8600, 75.6500),  # Bagru (Ajmer Road)
            (26.7800, 75.7200),  # Vatika / Diggi Road
            (26.7400, 75.8400),  # Shivdaspura / Tonk Road
            (26.7900, 75.9400),  # Bassi
            (26.8700, 75.9800),  # Agra Road Junction
        ],
    },
    {
        "name": "JNPT Port Container Expansion & Coastal Highway",
        "type": "Port",
        "agency": "Jawaharlal Nehru Port Authority / CIDCO",
        "states": ["Maharashtra"],
        "districts": ["Raigad", "Thane"],
        "land_required_ha": 290.0,
        "land_acquired_ha": 250.0,
        "target_date": date(2026, 11, 30),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (18.9500, 72.9500),  # Nhava Sheva Port
            (18.9100, 72.9900),  # Jasai / Dronagiri
            (18.8800, 73.0400),  # Chirle Interchange
            (18.9400, 73.1000),  # Panvel Creek
            (19.0200, 73.1100),  # Kalamboli / Thane link
        ],
    },
    {
        "name": "Delhi Metro Phase-IV Extension",
        "type": "Metro",
        "agency": "Delhi Metro Rail Corporation",
        "states": ["Delhi"],
        "districts": ["South Delhi", "South West Delhi"],
        "land_required_ha": 85.0,
        "land_acquired_ha": 52.0,
        "target_date": date(2027, 9, 30),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (28.5550, 77.1200),  # Aerocity Station
            (28.5400, 77.1400),  # Mahipalpur
            (28.5280, 77.1600),  # Vasant Kunj
            (28.5080, 77.1850),  # Chhatarpur
            (28.5120, 77.2150),  # Saket G-Block
            (28.5140, 77.2400),  # Khanpur / Neb Sarai
            (28.5100, 77.2650),  # Sangam Vihar
            (28.5100, 77.2950),  # Tughlakabad
        ],
    },
    {
        "name": "Amritsar-Jamnagar Expressway (Punjab Segment)",
        "type": "Highway",
        "agency": "National Highways Authority of India",
        "states": ["Punjab"],
        "districts": ["Amritsar", "Tarn Taran", "Moga", "Bathinda"],
        "land_required_ha": 250.0,
        "land_acquired_ha": 172.0,
        "target_date": date(2027, 3, 31),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (31.5200, 74.9800),  # Tibba (Amritsar border)
            (31.4200, 74.9500),  # Goindwal Sahib (Tarn Taran)
            (31.2500, 75.0200),  # Harike Pattan
            (30.9800, 75.1200),  # Dharamkot
            (30.8200, 75.1700),  # Moga / Baghapurana
            (30.4500, 75.0500),  # Bhagta Bhai Ka
            (30.2200, 74.9600),  # Rampura Phul / Bathinda
            (29.9800, 74.7500),  # Sangat / Punjab-Haryana border
        ],
    },
    {
        "name": "Punjab Dedicated Freight Corridor",
        "type": "Railway",
        "agency": "Dedicated Freight Corridor Corporation of India",
        "states": ["Punjab"],
        "districts": ["Ludhiana", "Patiala"],
        "land_required_ha": 180.0,
        "land_acquired_ha": 115.0,
        "target_date": date(2027, 8, 31),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (30.8500, 75.9800),  # Sahnewal (Ludhiana)
            (30.8000, 76.0800),  # Doraha
            (30.7000, 76.2200),  # Khanna
            (30.6300, 76.3800),  # Sirhind Junction
            (30.4900, 76.5900),  # Rajpura Yard (Patiala)
            (30.4400, 76.7200),  # Shambhu Border
        ],
    },
    {
        "name": "Nagpur-Mumbai Expressway (Samruddhi Mahamarg)",
        "type": "Highway",
        "agency": "Maharashtra State Road Development Corporation",
        "states": ["Maharashtra"],
        "districts": ["Nagpur", "Nashik", "Thane"],
        "land_required_ha": 380.0,
        "land_acquired_ha": 322.0,
        "target_date": date(2026, 10, 31),
        "status": ProjectStatus.ACTIVE.value,
        "waypoints": [
            (21.0500, 78.9500),  # Shivmadka (Nagpur)
            (20.7500, 78.6000),  # Wardha Sector
            (20.3000, 77.2000),  # Washim / Karanja
            (19.8500, 75.3500),  # Chhatrapati Sambhaji Nagar
            (19.9200, 74.2500),  # Kopargaon
            (19.8500, 73.9900),  # Sinnar (Nashik)
            (19.6800, 73.5500),  # Igatpuri Ghats
            (19.4500, 73.3300),  # Shahapur (Thane)
            (19.3100, 73.1200),  # Amane / Bhiwandi Terminal
        ],
    },
    {
        "name": "Barmer Refinery Township & Industrial Zone",
        "type": "Industrial",
        "agency": "HPCL Rajasthan Refinery Limited / RIICO",
        "states": ["Rajasthan"],
        "districts": ["Balotra", "Barmer", "Jodhpur"],
        "land_required_ha": 280.0,
        "land_acquired_ha": 82.0,
        "target_date": date(2028, 4, 30),
        "status": ProjectStatus.PLANNING.value,
        "waypoints": [
            (25.9200, 72.2400),  # Pachpadra Refinery Complex
            (25.8800, 72.2300),  # Sambhra Petrochemical Zone
            (25.8400, 72.2400),  # Balotra Industrial Township
            (25.8200, 72.3100),  # Asotra Corridor
            (25.9500, 72.5500),  # Kalyanpur Logistics Link
            (26.1500, 72.8500),  # Jodhpur Highway Link
        ],
    },
]


def seed_demo(db, user_map: dict[str, User]) -> None:
    """Generate 12 rich ground-truth multi-state infrastructure corridors and 2,400 linear right-of-way parcels."""
    print("\n--- Generating Audited Procedural Demo Corridors (12 National Infrastructure Projects) ---")
    admin_user = user_map["admin"]
    field_user = user_map["field_officer"]

    created_projects: list[Project] = []
    for pdata in PROJECTS_AUDIT_DATA:
        existing = db.execute(select(Project).where(Project.name == pdata["name"])).scalar_one_or_none()
        corridor_wkt = generate_linestring_wkt(pdata["waypoints"])
        if not existing:
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
            print(f"   + Created project: {proj.name} [Agency: {pdata['agency']}]")
        else:
            # Update existing project with audited corridors and metadata
            existing.type = pdata["type"]
            existing.states = pdata["states"]
            existing.districts = pdata["districts"]
            existing.land_required_ha = pdata["land_required_ha"]
            existing.land_acquired_ha = pdata["land_acquired_ha"]
            existing.target_date = pdata["target_date"]
            existing.status = pdata["status"]
            existing.corridor_geometry = WKTElement(corridor_wkt, srid=4326)
            created_projects.append(existing)
            print(f"   = Updated project: {existing.name}")

    db.commit()
    for p in created_projects:
        db.refresh(p)

    parcels_per_project = 200
    print(f"\n--- Generating {len(created_projects) * parcels_per_project} Linear Right-of-Way Parcels across {len(created_projects)} Corridors ---")
    stage_choices = [s.value for s in STAGE_ORDER]
    stage_weights = [0.08, 0.10, 0.12, 0.12, 0.14, 0.10, 0.10, 0.08, 0.06, 0.06, 0.04]
    now_utc = datetime.now(timezone.utc)
    today = now_utc.date()

    for p_idx, proj in enumerate(created_projects):
        pdata = PROJECTS_AUDIT_DATA[p_idx]
        waypoints = pdata["waypoints"]

        # Filter candidate districts matching this project
        proj_district_cfgs = [d for d in DISTRICT_CONFIGS if d["district"] in proj.districts and d["state"] in proj.states]
        if not proj_district_cfgs:
            proj_district_cfgs = [d for d in DISTRICT_CONFIGS if d["district"] in proj.districts or d["state"] in proj.states]
        if not proj_district_cfgs:
            proj_district_cfgs = DISTRICT_CONFIGS[:2]

        p_batch, s_batch, c_batch = [], [], []

        for i in range(parcels_per_project):
            fraction = (i + 0.5) / parcels_per_project
            lat_c, lon_c, _, _, _, _ = interpolate_corridor(waypoints, fraction)

            # Find nearest district along corridor path
            def dist_sq(d):
                return (d["center_lat"] - lat_c)**2 + (d["center_lon"] - lon_c)**2

            dcfg = min(proj_district_cfgs, key=dist_sq)
            village = dcfg["villages"][i % len(dcfg["villages"])]
            owner = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

            # Authentic cadastral naming (Survey in Maharashtra, Khasra elsewhere)
            if dcfg["state"] == "Maharashtra":
                survey_num = f"Survey {12 + (i % 220)}/{1 + (i % 8)}"
            else:
                survey_num = f"Khasra {12 + (i % 220)}/{1 + (i % 8)}"

            area_ha = round(random.uniform(0.20, 2.50), 3)
            stage = random.choices(stage_choices, weights=stage_weights)[0]
            stage_idx = [s.value for s in STAGE_ORDER].index(stage)

            if stage in (StageName.CLOSURE.value, StageName.POSSESSION.value):
                status = ParcelStatus.COMPLETED.value
                risk_score = round(random.uniform(2.0, 14.0), 1)
            elif stage in (StageName.OBJECTION.value, StageName.REHABILITATION_RESETTLEMENT.value) and (i % 9 == 0):
                status = ParcelStatus.BLOCKED.value
                risk_score = round(random.uniform(75.0, 94.0), 1)
            elif (i % 7 == 0):
                status = ParcelStatus.IN_PROGRESS.value
                risk_score = round(random.uniform(70.0, 88.0), 1)
            else:
                status = ParcelStatus.IN_PROGRESS.value
                risk_score = round(random.uniform(12.0, 58.0), 1)

            parcel_id = deterministic_uuid("pcl", f"{proj.name}:{i}")
            geom_wkt = generate_linear_cadastral_polygon_wkt(waypoints, fraction, i)

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
                assigned_officer=field_user.id if random.random() < 0.75 else None,
                created_at=now_utc - timedelta(days=random.randint(30, 280)),
            )
            p_batch.append(parcel)

            # Workflow stages 1 to 11
            for s_order, s_enum in enumerate(STAGE_ORDER, start=1):
                s_name = s_enum.value
                if s_order <= stage_idx:
                    s_status = StageStatus.COMPLETED.value
                    s_start = today - timedelta(days=(stage_idx - s_order + 1) * 30 + 15)
                    s_target = s_start + timedelta(days=30)
                    s_comp = s_start + timedelta(days=25)
                elif s_order == stage_idx + 1:
                    s_status = StageStatus.IN_PROGRESS.value if status != ParcelStatus.BLOCKED.value else StageStatus.BLOCKED.value
                    if risk_score >= 70:
                        s_target = today - timedelta(days=random.randint(2, 14))
                    elif risk_score >= 50:
                        s_target = today + timedelta(days=random.randint(1, 7))
                    else:
                        s_target = today + timedelta(days=random.randint(15, 60))
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
                        remarks="Statutory stage milestone",
                    )
                )

            # Compensation assessment & disbursement
            if stage_idx >= [s.value for s in STAGE_ORDER].index(StageName.AWARD.value):
                land_val = round(area_ha * random.uniform(3000000, 8000000), 2)
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
                        remarks="RFCTLARR statutory award calculation.",
                    )
                )

        db.add_all(p_batch)
        db.add_all(s_batch)
        db.add_all(c_batch)
        db.commit()
        print(f"   [OK] Seeded {len(p_batch)} linear cadastral parcels for: {proj.name[:42]}...")

        # Timeline snapshots
        snap_batch = []
        for h_idx in range(6):
            h_date = (now_utc - timedelta(days=(6 - h_idx) * 15)).date()
            comp_pct = max(0.08, min(0.95, (h_idx + 1) / 7))
            snap_batch.append(
                ProjectHistory(
                    snapshot_id=deterministic_uuid("snap", f"{proj.name}:{h_idx}"),
                    project_id=proj.project_id,
                    snapshot_date=h_date,
                    land_required_ha=proj.land_required_ha,
                    land_acquired_ha=round(proj.land_required_ha * comp_pct * 0.7, 2),
                    parcels_total=parcels_per_project,
                    parcels_completed=int(parcels_per_project * comp_pct * 0.7),
                    parcels_in_progress=int(parcels_per_project * 0.4),
                    parcels_disputed=random.randint(2, 8),
                    compensation_paid_total=round(proj.land_required_ha * 3000000 * comp_pct, 2),
                    compensation_pending_total=round(proj.land_required_ha * 1200000, 2),
                    stages_snapshot={"SURVEY": 25, "VERIFICATION": 20, "AWARD": 18, "COMPENSATION": 15},
                    metadata_json={
                        "pending_parcels": 25.0,
                        "completed_parcels": 22.0,
                        "average_stage_days": 35.0,
                        "sla_breaches": 3.0,
                        "compensation_pending": 7.0,
                        "rr_pending": 4.0,
                        "possession_pending": 2.0,
                        "processing_rate": 0.22,
                        "officers_count": 4,
                    },
                )
            )
        db.add_all(snap_batch)
        db.commit()


def seed_alerts(db) -> None:
    """Seed statutory SLA warnings, high-risk parcel alerts, and incident flags."""
    print("\n--- Seeding Statutory & SLA Alerts ---")
    projects = db.execute(select(Project)).scalars().all()
    if not projects:
        return

    p_by_name = {p.name: p for p in projects}
    alerts_data = [
        {
            'proj': 'Delhi Metro Phase-IV Extension',
            'title': 'Sec 19 Declaration 12-Month Statutory Lapse Warning',
            'message': 'Section 19 declaration must be published within 12 months of Section 11 preliminary notification under RFCTLARR 2013 Section 19(7) for South Delhi parcels. 18 days remaining before statutory lapse.',
            'severity': 'CRITICAL',
            'issue_type': 'Statutory SLA Breach',
            'time_ago': '18m ago',
        },
        {
            'proj': 'Delhi-Meerut RRTS Corridor',
            'title': 'High Court Writ Petition: Injunction Hearing Listed',
            'message': 'Writ Petition (Civil) No. 4921/2026 listed before Delhi High Court challenging acquisition compensation multiplier for peri-urban parcels in East Delhi and Sahibabad (Ghaziabad).',
            'severity': 'CRITICAL',
            'issue_type': 'Legal / Court Stay',
            'time_ago': '45m ago',
        },
        {
            'proj': 'Amritsar-Jamnagar Expressway (Punjab Segment)',
            'title': 'Sec 15 Objection Overdue: SLA Exceeded by 22 Days',
            'message': '42 statutory objections filed under Section 15(1) across Tarn Taran and Amritsar alignment have exceeded the mandatory 60-day disposal timeline. DLAO hearing report pending.',
            'severity': 'CRITICAL',
            'issue_type': 'SLA Overdue',
            'time_ago': '1h ago',
        },
        {
            'proj': 'Western Dedicated Freight Corridor (WDFC - Phase 2)',
            'title': 'DBT Compensation Transfer Failure: 14 Beneficiary Accounts',
            'message': 'PFMS batch payout error: Aadhaar bank account mismatch detected for 14 awardees in Marwar (Pali) division. Manual reconciliation required.',
            'severity': 'CRITICAL',
            'issue_type': 'DBT Payment Error',
            'time_ago': '2h ago',
        },
        {
            'proj': 'Nagpur-Mumbai Expressway (Samruddhi Mahamarg)',
            'title': 'Joint Measurement Survey Discrepancy Flagged',
            'message': 'Cadastral overlay reveals 3.4 hectare overlap between survey numbers 142 and 144 in Thane (Shahapur) district. Joint inspection with revenue inspector scheduled.',
            'severity': 'WARNING',
            'issue_type': 'Survey Discrepancy',
            'time_ago': '3h ago',
        },
        {
            'proj': 'Jaipur Ring Road & Multimodal Logistics Hub',
            'title': 'Environmental & Forest Clearance NOC Pending',
            'message': 'Stage-1 Forest clearance submission awaiting State Forest Advisory Committee review for 18.2 hectares of reserve forest diversion in Bassi tehsil, Jaipur.',
            'severity': 'WARNING',
            'issue_type': 'Clearance Delay',
            'time_ago': '5h ago',
        },
        {
            'proj': 'Punjab Dedicated Freight Corridor',
            'title': 'Collector Award Assessment (Sec 23) Approved',
            'message': 'DLAO Patiala has finalized compensation assessment matrix under RFCTLARR First Schedule for Rajpura yard. Total disbursement sanctioned: Rs 48.6 Crores.',
            'severity': 'INFO',
            'issue_type': 'Statutory Approval',
            'time_ago': '7h ago',
        },
        {
            'proj': 'Mumbai-Ahmedabad High Speed Rail (MAHSR Bullet Train)',
            'title': 'Physical Possession Handover Completed for Palghar Sector',
            'message': 'Section 38 possession certificate executed for 84 linear parcels across Boisar and Talasari. ROW clearance certificate dispatched to NHSRCL.',
            'severity': 'INFO',
            'issue_type': 'Possession Taken',
            'time_ago': '12h ago',
        },
        {
            'proj': 'Barmer Refinery Township & Industrial Zone',
            'title': 'Grievance Redressal Committee Hearing Escalated',
            'message': 'R&R entitlement claims regarding rehabilitation package allocation disputed by 19 displaced families in Pachpadra tehsil, Balotra.',
            'severity': 'WARNING',
            'issue_type': 'R&R Grievance',
            'time_ago': '1d ago',
        },
        {
            'proj': 'JNPT Port Container Expansion & Coastal Highway',
            'title': 'CRZ Coastal Regulation Zone Clearance Endorsement',
            'message': 'Maharashtra Coastal Zone Management Authority (MCZMA) has issued formal recommendation for Raigad (Uran / Jasai) coastal bypass alignment.',
            'severity': 'INFO',
            'issue_type': 'Statutory Clearance',
            'time_ago': '1d ago',
        },
        {
            'proj': 'Pune Ring Road (Eastern & Western Alignment)',
            'title': 'Arbitration Award Appeal Filed under Section 64',
            'message': 'Commercial landholder has filed reference to Land Acquisition, Rehabilitation and Resettlement Authority (LARRA) seeking enhanced market valuation in Mulshi tehsil.',
            'severity': 'CRITICAL',
            'issue_type': 'LARRA Reference',
            'time_ago': '2d ago',
        },
        {
            'proj': 'Delhi-Mumbai Expressway (Vadodara-Mumbai Section)',
            'title': 'Sec 11 Preliminary Notification Gazette Published',
            'message': 'Official Gazette Notification published in 2 regional daily newspapers and public portal for Wada and Bhiwandi packages. 60-day objection window now active.',
            'severity': 'INFO',
            'issue_type': 'Gazette Publication',
            'time_ago': '3d ago',
        },
    ]

    now = datetime.now(timezone.utc)
    for idx, ad in enumerate(alerts_data):
        p = p_by_name.get(ad['proj'])
        if not p:
            continue
        parcel = db.execute(select(Parcel).where(Parcel.project_id == p.project_id).limit(1)).scalar_one_or_none()
        a = Alert(
            alert_id=deterministic_uuid("alert", f"{ad['proj']}:{idx}"),
            user_id=None,
            project_id=p.project_id,
            parcel_id=parcel.parcel_id if parcel else None,
            title=ad['title'],
            message=ad['message'],
            severity=ad['severity'],
            is_read=False,
            metadata_json={
                'project_name': p.name,
                'issue_type': ad['issue_type'],
                'time_ago': ad['time_ago'],
                'state': p.states[0] if p.states else 'National',
            },
            created_at=now - timedelta(hours=idx * 3 + 1),
        )
        existing = db.execute(select(Alert).where(Alert.alert_id == a.alert_id)).scalar_one_or_none()
        if not existing:
            db.add(a)

    db.commit()
    print("   + Seeded 12 statutory and SLA alerts.")


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

        seed_alerts(db)

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

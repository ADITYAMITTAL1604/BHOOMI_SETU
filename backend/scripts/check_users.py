"""Verify RBAC scope filtering works correctly after the fix."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv(str(Path(__file__).resolve().parent.parent.parent / ".env"))
from sqlalchemy import create_engine, text
engine = create_engine(os.environ["DATABASE_URL"])

with engine.connect() as conn:
    print("=== UPDATED DOCUMENT-PARCEL-PROJECT MAPPING ===")
    rows = conn.execute(text("""
        SELECT d.title, p.state AS parcel_state, p.district AS parcel_district,
               proj.name AS project_name, proj.states AS project_states,
               u.username AS uploader, u.state_scope AS uploader_state
        FROM documents d
        LEFT JOIN parcels p ON d.parcel_id = p.parcel_id
        LEFT JOIN projects proj ON d.project_id = proj.project_id
        LEFT JOIN users u ON d.uploaded_by = u.id
        ORDER BY d.title
    """)).fetchall()
    for r in rows:
        print(f"  {r[0]}")
        print(f"    parcel: {r[1]}/{r[2]}  project: {r[3]}  states={r[4]}")
        print(f"    uploader: {r[5]} (scope: {r[6]})")

    print("\n=== EXPECTED VISIBILITY PER USER ===")
    print("field_officer (UP/Ghaziabad): should see 2 docs (Joint Measurement + Section 23 Award)")
    print("punjab_state (Punjab): should see 1 doc (Section 15 Objection)")
    print("delhi_state (Delhi): should see 2 docs (Joint Measurement + Section 23 - via project states)")
    print("admin: should see ALL 5 docs")

    print("\n=== DOCUMENTS VISIBLE TO GHAZIABAD field_officer (district=Ghaziabad) ===")
    rows = conn.execute(text("""
        SELECT d.title
        FROM documents d
        LEFT JOIN parcels p ON d.parcel_id = p.parcel_id
        LEFT JOIN projects proj ON d.project_id = proj.project_id
        WHERE (p.district = 'Ghaziabad')
           OR ('Ghaziabad' = ANY(proj.districts))
        ORDER BY d.title
    """)).fetchall()
    for r in rows:
        print(f"  - {r[0]}")
    if not rows:
        print("  (none)")

    print("\n=== DOCUMENTS VISIBLE TO punjab_state (state=Punjab) ===")
    rows = conn.execute(text("""
        SELECT d.title
        FROM documents d
        LEFT JOIN parcels p ON d.parcel_id = p.parcel_id
        LEFT JOIN projects proj ON d.project_id = proj.project_id
        WHERE (p.state = 'Punjab')
           OR ('Punjab' = ANY(proj.states))
        ORDER BY d.title
    """)).fetchall()
    for r in rows:
        print(f"  - {r[0]}")
    if not rows:
        print("  (none)")

    print("\n=== DOCUMENTS VISIBLE TO delhi_state (state=Delhi) ===")
    rows = conn.execute(text("""
        SELECT d.title
        FROM documents d
        LEFT JOIN parcels p ON d.parcel_id = p.parcel_id
        LEFT JOIN projects proj ON d.project_id = proj.project_id
        WHERE (p.state = 'Delhi')
           OR ('Delhi' = ANY(proj.states))
        ORDER BY d.title
    """)).fetchall()
    for r in rows:
        print(f"  - {r[0]}")
    if not rows:
        print("  (none)")

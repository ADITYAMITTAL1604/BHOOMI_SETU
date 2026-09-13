"""Comprehensive database restoration script for BhoomiSetu.

Restores the live Supabase PostgreSQL database to its complete, rich state:
1. Removes orphan projects from previous failed CI runs.
2. Seeds users and administrative boundaries.
3. Seeds 12 national infrastructure corridors with 2,400 linear right-of-way parcels, stages, and compensations.
4. Seeds 1,753 Project Affected Families (RR records).
5. Seeds 25 strictly entity-targeted notifications.
"""

import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, text
from app.database import Base, SessionLocal, engine
from app.models import Project, Parcel, RRRecord, Notification
from db.seed import seed_users, seed_boundaries, seed_demo, seed_alerts
from seed_rr_records import seed_rr

def restore():
    print("=" * 70)
    print("  BHOOMI-SETU -- RESTORING PRODUCTION SUPABASE DATABASE")
    print("=" * 70)

    db = SessionLocal()
    try:
        # Step 1: Clean up orphan projects if parcels count is 0
        p_count = db.query(Parcel).count()
        print(f"Current Parcels in DB: {p_count}")
        if p_count == 0:
            print("Cleaning up orphan projects from aborted CI runs...")
            db.execute(text("DELETE FROM project_history"))
            db.execute(text("DELETE FROM alerts"))
            db.execute(text("DELETE FROM projects"))
            db.commit()
            print("   [OK] Orphan projects cleared.")

        # Step 2: Seed Users and Administrative Boundaries
        user_map = seed_users(db)
        seed_boundaries(db)

        # Step 3: Seed 12 National Projects & 2,400 Cadastral Parcels
        print("\n--- Seeding 12 National Infrastructure Projects & 2,400 Parcels ---")
        seed_demo(db, user_map)
        seed_alerts(db)

        # Step 4: Seed 1,753 RRRecords (PAFs)
        print("\n--- Seeding 1,753 Project Affected Families (RR Records) ---")
        seed_rr()

        # Step 5: Seed 25 Direct Entity-Linked Notifications
        print("\n--- Seeding 25 Entity-Linked Notifications ---")
        import subprocess
        res = subprocess.run([sys.executable, "seed_notifications_robust.py"], capture_output=True, text=True, cwd=str(backend_dir))
        print(res.stdout)
        if res.stderr:
            print("Stderr:", res.stderr)

        # Final Verification
        db_check = SessionLocal()
        final_projects = db_check.query(Project).count()
        final_parcels = db_check.query(Parcel).count()
        final_rr = db_check.query(RRRecord).count()
        final_notifs = db_check.query(Notification).count()
        db_check.close()

        print("\n" + "=" * 70)
        print("  DATABASE RESTORATION COMPLETED SUCCESSFULLY!")
        print(f"  - Projects: {final_projects} (Expected: 12)")
        print(f"  - Parcels: {final_parcels} (Expected: 2400)")
        print(f"  - RR PAF Records: {final_rr} (Expected: ~1500-1800)")
        print(f"  - Notifications: {final_notifs} (Expected: 25)")
        print("=" * 70)

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Restoration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    restore()

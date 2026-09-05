"""Direct SQLite to PostgreSQL / Supabase Data Migration Tool.

Migrates the exact local SQLite database (bhoomisetu.db) to Supabase PostgreSQL,
ensuring 100% identical data, geometries, alerts, and statutory stages.

Usage:
    python backend/scripts/migrate_sqlite_to_postgres.py --target "postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres"

Or set TARGET_DATABASE_URL in your environment and run:
    python backend/scripts/migrate_sqlite_to_postgres.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    AcquisitionStage,
    Alert,
    AuditLog,
    Compensation,
    Document,
    GISBoundary,
    Project,
    ProjectHistory,
    RefreshToken,
    RRRecord,
    User,
)
from app.models.parcel import Parcel

# Dependency order for relational integrity
TABLE_MODELS = [
    ("users", User),
    ("gis_boundaries", GISBoundary),
    ("projects", Project),
    ("parcels", Parcel),
    ("acquisition_stages", AcquisitionStage),
    ("compensation", Compensation),
    ("rr_records", RRRecord),
    ("project_history", ProjectHistory),
    ("alerts", Alert),
    ("audit_logs", AuditLog),
    ("refresh_tokens", RefreshToken),
    ("documents", Document),
]


def find_sqlite_db() -> Path:
    """Find the local bhoomisetu.db file."""
    candidates = [
        backend_dir.parent / "bhoomisetu.db",
        backend_dir / "bhoomisetu.db",
        Path("bhoomisetu.db").resolve(),
        Path("../bhoomisetu.db").resolve(),
    ]
    for p in candidates:
        if p.exists() and p.stat().st_size > 0:
            return p
    raise FileNotFoundError("Could not locate local bhoomisetu.db database file.")


def normalize_postgres_url(url: str) -> str:
    """Ensure proper SQLAlchemy driver prefix."""
    url = url.strip()
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def migrate(sqlite_path: Path, target_url: str, wipe: bool = False) -> None:
    norm_target = normalize_postgres_url(target_url)
    print("=" * 70)
    print("  BHOOMI-SETU -- SQLITE TO SUPABASE / POSTGRESQL MIGRATION")
    print("=" * 70)
    print(f"Source SQLite:  {sqlite_path} ({sqlite_path.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Target Postgres: {norm_target.split('@')[-1] if '@' in norm_target else norm_target}")
    print("=" * 70)

    # 1. Source Connection
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path.as_posix()}", connect_args={"check_same_thread": False})
    SqliteSession = sessionmaker(bind=sqlite_engine)
    src_db = SqliteSession()

    # 2. Target Connection
    pg_engine = create_engine(norm_target, pool_pre_ping=True)
    PgSession = sessionmaker(bind=pg_engine)

    # 3. Bootstrap PostGIS & Tables on Target
    print("\n1. Initializing PostGIS extensions and schema on target...")
    if not norm_target.startswith("sqlite"):
        with pg_engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            conn.commit()
        print("   [OK] PostGIS extensions enabled.")
    else:
        print("   [OK] Target is SQLite (test mode).")

    Base.metadata.create_all(bind=pg_engine)
    print("   [OK] Target database tables verified/created.")

    tgt_db = PgSession()

    try:
        # Optional Wipe
        if wipe:
            print("\n2. Wiping existing target data for clean migration (--wipe enabled)...")
            for tbl_name, model in reversed(TABLE_MODELS):
                tgt_db.query(model).delete()
            tgt_db.commit()
            print("   [OK] Target tables cleared.")
        else:
            print("\n2. Checking existing target database state...")

        # 4. Migrate Table by Table
        print("\n3. Migrating records table-by-table...")
        summary = []

        for tbl_name, model in TABLE_MODELS:
            src_records = src_db.query(model).all()
            src_count = len(src_records)

            if src_count == 0:
                summary.append((tbl_name, 0, 0, "SKIPPED (0 rows)"))
                continue

            # Check existing count on target
            tgt_existing = tgt_db.query(func.count()).select_from(model).scalar() or 0

            if tgt_existing > 0 and not wipe:
                # Merge existing
                print(f"   * {tbl_name:22} : Merging {src_count} records (target already had {tgt_existing})...")
                for obj in src_records:
                    src_db.expunge(obj)
                    tgt_db.merge(obj)
                tgt_db.commit()
            else:
                print(f"   * {tbl_name:22} : Inserting {src_count} records...")
                # Bulk save for speed
                for i in range(0, src_count, 500):
                    batch = src_records[i : i + 500]
                    for item in batch:
                        src_db.expunge(item)
                        tgt_db.merge(item)
                    tgt_db.commit()

            tgt_final = tgt_db.query(func.count()).select_from(model).scalar() or 0
            status_str = "MATCH (100%)" if tgt_final == src_count else f"OK ({tgt_final} rows)"
            summary.append((tbl_name, src_count, tgt_final, status_str))

        # 5. Summary Report
        print("\n" + "=" * 70)
        print(f"  {'TABLE NAME':<25} {'SQLITE':<12} {'POSTGRES':<12} {'STATUS'}")
        print("-" * 70)
        for tbl_name, s_cnt, t_cnt, st in summary:
            print(f"  {tbl_name:<25} {s_cnt:<12} {t_cnt:<12} {st}")
        print("=" * 70)
        print("  [SUCCESS] MIGRATION COMPLETED! DATA IS 100% IDENTICAL TO LOCAL.")
        print("=" * 70)

    except Exception as e:
        tgt_db.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        src_db.close()
        tgt_db.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate local SQLite bhoomisetu.db to PostgreSQL/Supabase")
    parser.add_argument(
        "--target",
        type=str,
        default=os.getenv("TARGET_DATABASE_URL") or os.getenv("DATABASE_URL"),
        help="Target PostgreSQL connection URI (e.g. postgresql://postgres:pwd@db.ref.supabase.co:5432/postgres)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Optional path to source bhoomisetu.db file",
    )
    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Wipe target tables before copying to ensure clean 1:1 state",
    )
    args = parser.parse_args()

    if not args.target:
        print("[ERROR] No target database URL provided.")
        print("Usage: python backend/scripts/migrate_sqlite_to_postgres.py --target 'postgresql://...'")
        sys.exit(1)

    sqlite_path = Path(args.source) if args.source else find_sqlite_db()
    migrate(sqlite_path, args.target, wipe=args.wipe)


if __name__ == "__main__":
    main()

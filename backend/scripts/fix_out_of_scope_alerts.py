"""
One-off maintenance script: fixes existing Alert rows that are directly
addressed to a user (user_id set) but whose linked project/parcel falls
outside that user's state/district scope.

This cleans up historical data created before the scope-aware alert fix
(e.g. by ad-hoc scripts like update_alerts.py that attached parcels to
alerts without checking the target user's jurisdiction).

For each out-of-scope alert found, the script will (default) DELETE it.
Pass --dry-run to only report what would change, with no writes.

Usage (from backend/ directory):
    python scripts/fix_out_of_scope_alerts.py --dry-run
    python scripts/fix_out_of_scope_alerts.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running as `python scripts/fix_out_of_scope_alerts.py` from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Alert, Parcel, Project, User


def user_in_scope(user: User, *, state: str | None, district: str | None) -> bool:
    if user.district_scope:
        return bool(district) and user.district_scope == district
    if user.state_scope:
        return bool(state) and user.state_scope == state
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Report only, don't modify the database.")
    args = parser.parse_args()

    db = SessionLocal()
    removed = 0
    checked = 0

    try:
        alerts = db.execute(
            select(Alert).where(Alert.user_id.isnot(None))
        ).scalars().all()

        for alert in alerts:
            user = db.get(User, alert.user_id)
            if not user:
                continue

            # Only alerts tied to a specific location can be out of scope.
            state = None
            district = None

            if alert.parcel_id:
                parcel = db.get(Parcel, alert.parcel_id)
                if parcel:
                    state = parcel.state or None
                    district = parcel.district or None
            elif alert.project_id:
                project = db.get(Project, alert.project_id)
                if project:
                    if project.states:
                        state = project.states[0]
                    if project.districts:
                        district = project.districts[0]

            if state is None and district is None:
                continue  # No location attached — always fine.

            checked += 1
            if not user_in_scope(user, state=state, district=district):
                print(
                    f"[OUT OF SCOPE] alert_id={alert.alert_id} user={user.username} "
                    f"(state_scope={user.state_scope}, district_scope={user.district_scope}) "
                    f"-> alert location state={state}, district={district} :: {alert.title!r}"
                )
                if not args.dry_run:
                    db.delete(alert)
                removed += 1

        if not args.dry_run:
            db.commit()

        print(f"\nChecked {checked} location-linked alert(s). "
              f"{'Would remove' if args.dry_run else 'Removed'} {removed}.")
        if args.dry_run and removed:
            print("Re-run without --dry-run to apply the deletion.")

    finally:
        db.close()


if __name__ == "__main__":
    main()

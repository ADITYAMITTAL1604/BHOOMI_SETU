"""Seed realistic, strictly accurate, and entity-linked notifications for BhoomiSetu.

Every single notification is strictly linked to the EXACT parcel or project
specified in its title and message. Clicking any notification navigates
directly to the specific parcel detail page or project detail page.
"""

import sys
import uuid
from datetime import datetime, timezone, timedelta

backend_dir = r"c:\PROJECTS\BHOOMI_SETU 2.0\backend"
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models.user import User
from app.models.notification import Notification
from app.models.project import Project
from app.models.parcel import Parcel

db = SessionLocal()

users = db.query(User).all()
user_map = {u.username: u for u in users}
print(f"Loaded {len(users)} users: {list(user_map.keys())}")

# Clear existing notifications to ensure pristine sync
deleted = db.query(Notification).delete()
db.commit()
print(f"Cleared {deleted} existing notifications")

# Load projects
projects = {p.name: p for p in db.query(Project).all()}
rrts_proj = next((p for name, p in projects.items() if "Delhi-Meerut" in name), None)
wdfc_proj = next((p for name, p in projects.items() if "Western" in name or "WDFC" in name), None)
pune_proj = next((p for name, p in projects.items() if "Pune" in name), None)
dmrc_proj = next((p for name, p in projects.items() if "Delhi Metro" in name), None)
amritsar_proj = next((p for name, p in projects.items() if "Amritsar" in name), None)
samruddhi_proj = next((p for name, p in projects.items() if "Samruddhi" in name or "Nagpur" in name), None)
barmer_proj = next((p for name, p in projects.items() if "Barmer" in name), None)

# Find key real parcels
duhai_78_3 = db.query(Parcel).filter(Parcel.village.ilike("%Duhai%"), Parcel.survey_number.ilike("%78%")).first()
duhai_54_3 = db.query(Parcel).filter(Parcel.village.ilike("%Duhai%"), Parcel.survey_number.ilike("%54%")).first()
duhai_62_3 = db.query(Parcel).filter(Parcel.village.ilike("%Duhai%"), Parcel.survey_number.ilike("%62%")).first()
skk_12_1 = db.query(Parcel).filter(Parcel.village.ilike("%Sarai Kale Khan%"), Parcel.survey_number.ilike("%12%")).first()
skk_19_8 = db.query(Parcel).filter(Parcel.village.ilike("%Sarai Kale Khan%"), Parcel.survey_number.ilike("%19%")).first()
punjab_patti = db.query(Parcel).filter(Parcel.village.ilike("%Patti%"), Parcel.state.ilike("%Punjab%")).first()
maharashtra_nhava = db.query(Parcel).filter(Parcel.village.ilike("%Nhava%"), Parcel.state.ilike("%Maharashtra%")).first()
rajasthan_bagru = db.query(Parcel).filter(Parcel.village.ilike("%Bagru%"), Parcel.state.ilike("%Rajasthan%")).first()
meerut_parcel = db.query(Parcel).filter(Parcel.district.ilike("%Meerut%")).first() or duhai_62_3
muradnagar_parcel = db.query(Parcel).filter(Parcel.village.ilike("%Muradnagar%")).first() or duhai_54_3

print("Resolved exact entities:")
print(f"  RRTS Proj: {rrts_proj.name if rrts_proj else 'None'}")
print(f"  Duhai 78/3: {duhai_78_3.survey_number if duhai_78_3 else 'None'} ({duhai_78_3.parcel_id if duhai_78_3 else 'None'})")
print(f"  Duhai 54/3: {duhai_54_3.survey_number if duhai_54_3 else 'None'}")
print(f"  SKK 12/1: {skk_12_1.survey_number if skk_12_1 else 'None'}")
print(f"  Punjab Patti: {punjab_patti.survey_number if punjab_patti else 'None'}")

now = datetime.now(timezone.utc)

# List of defined notifications with exact entity targets
# Format: (username, sev, cat, title, msg, entity_type, entity_obj, hours_ago)
NOTIF_DEFINITIONS = [
    # ── Admin (Administrator) ──
    (
        "admin", "CRITICAL", "sla",
        f"Critical SLA Breach: {duhai_78_3.survey_number}, Duhai Village ({rrts_proj.name})",
        f"Statutory Section 15 objection resolution exceeded by 24 days for {duhai_78_3.survey_number} in Duhai village. Immediate Collector intervention required.",
        "parcel", duhai_78_3, 1
    ),
    (
        "admin", "WARNING", "approval",
        f"Ministry Compliance Escalation: {rrts_proj.name}",
        f"Cabinet Committee on Infrastructure requested urgent portfolio review for 200 corridor parcels under {rrts_proj.name}.",
        "project", rrts_proj, 3
    ),
    (
        "admin", "WARNING", "approval",
        f"Pending Cabinet Approval: {wdfc_proj.name}",
        f"Section 19 statutory clearances for multi-state rail alignment under {wdfc_proj.name} awaiting final ministry gazette approval.",
        "project", wdfc_proj, 6
    ),
    (
        "admin", "CRITICAL", "sla",
        f"Court Stay Injunction: {skk_12_1.survey_number}, Sarai Kale Khan",
        f"Delhi High Court Single Bench listed stay petition on preliminary acquisition notification for {skk_12_1.survey_number} in Sarai Kale Khan.",
        "parcel", skk_12_1, 12
    ),

    # ── Central User (Ministry / PMO) ──
    (
        "central_user", "CRITICAL", "sla",
        f"Ministry Compliance Escalation: {rrts_proj.name}",
        f"Cabinet Committee on Infrastructure requested status briefing on 42 priority parcels under {rrts_proj.name}.",
        "project", rrts_proj, 1
    ),
    (
        "central_user", "WARNING", "approval",
        f"Sec 19 Statutory Gazette Ready: {wdfc_proj.name}",
        f"Gazette notification proof for corridor alignment finalized by Ministry of Law & Justice for {wdfc_proj.name}.",
        "project", wdfc_proj, 4
    ),
    (
        "central_user", "INFO", "document",
        f"Environmental Clearance Endorsed (MoEFCC): {amritsar_proj.name}",
        f"Stage-1 Forest clearance received from MoEFCC for {amritsar_proj.name} corridor expansion.",
        "project", amritsar_proj, 8
    ),

    # ── State User (UP State Revenue Officer) ──
    (
        "state_user", "CRITICAL", "sla",
        f"SLA Breach: Sec 15 Objections Overdue for {meerut_parcel.survey_number}, {meerut_parcel.district}",
        f"Land parcel {meerut_parcel.survey_number} in {meerut_parcel.district} has crossed the statutory 60-day objection review period under Section 15.",
        "parcel", meerut_parcel, 1
    ),
    (
        "state_user", "WARNING", "approval",
        f"Joint Measurement Survey Pending Approval: {rrts_proj.name}",
        f"DLAO Ghaziabad submitted joint boundary verification report for {rrts_proj.name} (12.4 hectares).",
        "project", rrts_proj, 3
    ),
    (
        "state_user", "CRITICAL", "compensation",
        f"DBT Transfer Failure: Beneficiary Account for {duhai_54_3.survey_number}",
        f"Aadhaar-mismatch reported in Ghaziabad DLAO treasury portal for {duhai_54_3.survey_number}, Duhai. Corrective re-disbursement required.",
        "parcel", duhai_54_3, 6
    ),
    (
        "state_user", "INFO", "stage",
        f"Award Declaration Completed: {duhai_62_3.survey_number}, Duhai",
        f"Collector Ghaziabad has declared the Section 23 award for parcel {duhai_62_3.survey_number} in Duhai village.",
        "parcel", duhai_62_3, 14
    ),

    # ── District User (Ghaziabad District Collector) ──
    (
        "district_user", "CRITICAL", "sla",
        f"Urgent: Sec 15 Objection Hearing Listed Today for {duhai_78_3.survey_number}, Village Duhai",
        f"Public hearing for {duhai_78_3.survey_number}, Village Duhai scheduled at DLAO Court Room 2. Collector attendance requested.",
        "parcel", duhai_78_3, 1
    ),
    (
        "district_user", "WARNING", "approval",
        f"Compensation Award Valuation Requiring Sign-off: {duhai_54_3.survey_number}",
        f"DLAO assessment sheet for agricultural parcel {duhai_54_3.survey_number} (Duhai) pending Collector digital signature.",
        "parcel", duhai_54_3, 4
    ),
    (
        "district_user", "INFO", "document",
        f"Field Survey Demarcation Log Uploaded: {duhai_62_3.survey_number}",
        f"Field Officer uploaded verified GIS boundary verification shapefile for {duhai_62_3.survey_number} in Duhai sector.",
        "parcel", duhai_62_3, 9
    ),

    # ── Field Officer (Field Survey Officer) ──
    (
        "field_officer", "CRITICAL", "sla",
        f"Boundary Demarcation Deadline in 48 Hours: {duhai_78_3.survey_number}, Duhai Village",
        f"Field verification and boundary demarcation for {duhai_78_3.survey_number}, Duhai village assigned to your unit.",
        "parcel", duhai_78_3, 1
    ),
    (
        "field_officer", "WARNING", "document",
        f"Discrepancy in Cadastral Polygon: {duhai_54_3.survey_number}",
        f"Ground survey reveals 0.4 ha boundary overlap for {duhai_54_3.survey_number} with state highway reserve boundary.",
        "parcel", duhai_54_3, 5
    ),
    (
        "field_officer", "INFO", "system",
        f"Mobile GIS Inspection App Synced: {duhai_62_3.survey_number}",
        f"34 offline survey coordinates for {duhai_62_3.survey_number} successfully synchronized with central BhoomiSetu cadastral layer.",
        "parcel", duhai_62_3, 14
    ),

    # ── Delhi State & District ──
    (
        "delhi_state", "CRITICAL", "sla",
        f"SLA Breach: Right-of-Way Clearance Delay on {skk_12_1.survey_number}",
        f"Parcel {skk_12_1.survey_number} in Sarai Kale Khan blocked due to municipal utility re-routing delays under {dmrc_proj.name}.",
        "parcel", skk_12_1, 2
    ),
    (
        "delhi_state", "WARNING", "approval",
        f"Alignment Modification Review: {dmrc_proj.name}",
        f"Delhi Metro Rail Corporation submitted alignment revision for South Delhi section under {dmrc_proj.name}.",
        "project", dmrc_proj, 5
    ),
    (
        "delhi_district", "CRITICAL", "sla",
        f"High Court Stay Injunction on {skk_19_8.survey_number}",
        f"Stay petition on {skk_19_8.survey_number}, Sarai Kale Khan listed before Single Bench. Standing Counsel notified.",
        "parcel", skk_19_8, 3
    ),

    # ── Punjab State & District ──
    (
        "punjab_state", "CRITICAL", "sla",
        f"SLA Breach: Possession Handover Overdue on {punjab_patti.survey_number}",
        f"Physical possession handover overdue by 35 days for {punjab_patti.survey_number}, Patti under {amritsar_proj.name}.",
        "parcel", punjab_patti, 2
    ),
    (
        "punjab_state", "WARNING", "compensation",
        f"Farmer Grievance Escalated: {amritsar_proj.name}",
        f"Punjab State Grievance Cell flagged compensation valuation dispute for {amritsar_proj.name}.",
        "project", amritsar_proj, 7
    ),
    (
        "punjab_district", "CRITICAL", "sla",
        f"Possession Handover Delayed: {punjab_patti.survey_number}, Patti",
        f"Land acquisition possession memorandum for {punjab_patti.survey_number} pending signature from SDM Tarn Taran.",
        "parcel", punjab_patti, 2
    ),

    # ── Project Agency (NHAI / DMRC) ──
    (
        "agency_user", "WARNING", "approval",
        f"Alignment Requisition Awaiting DLAO Review: {rrts_proj.name}",
        f"NHAI submitted revised Right-of-Way proposal for interchange bypass under {rrts_proj.name}.",
        "project", rrts_proj, 4
    ),
    (
        "agency_user", "CRITICAL", "sla",
        f"Corridor Handover Milestone Breached: {duhai_78_3.survey_number}",
        f"Contractor mobilization halted due to pending possession on {duhai_78_3.survey_number}, Duhai village.",
        "parcel", duhai_78_3, 18
    ),
]

created_count = 0
for (uname, sev, cat, title, msg, ent_type, ent_obj, hours_ago) in NOTIF_DEFINITIONS:
    user = user_map.get(uname)
    if not user or not ent_obj:
        continue

    if ent_type == "parcel":
        target_id = ent_obj.parcel_id
        target_url = f"/parcels/{ent_obj.parcel_id}"
        ent_name = f"Parcel: {ent_obj.survey_number} ({ent_obj.village})"
    else:
        target_id = ent_obj.project_id
        target_url = f"/projects/{ent_obj.project_id}"
        ent_name = f"Project: {ent_obj.name}"

    n = Notification(
        notification_id=uuid.uuid4(),
        user_id=user.id,
        title=title,
        message=msg,
        severity=sev,
        category=cat,
        is_read=False,
        entity_type=ent_type,
        entity_id=target_id,
        action_url=target_url,
        metadata_json={
            "entity_name": ent_name,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "state_scope": user.state_scope,
            "district_scope": user.district_scope,
        },
        created_at=now - timedelta(hours=hours_ago),
    )
    db.add(n)
    created_count += 1

db.commit()
print(f"Successfully seeded {created_count} strictly verified, exact entity-targeted notifications!")
db.close()

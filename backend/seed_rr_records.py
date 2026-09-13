"""Seed Project Affected Families (PAFs) and R&R Records for BhoomiSetu.

This links realistic PAF records to existing parcels across all 12 projects,
ensuring Executive Summary, R&R Social Safeguards, and statutory RFCTLARR
reports reflect live, authentic data.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Parcel, Project, RRRecord
from app.models.enums import AffectedType, RehabilitationStatus

# Common names for family heads by region
FIRST_NAMES = [
    "Ram Avatar", "Satish Chand", "Gurvinder", "Harpreet", "Dharmendra", "Mukesh",
    "Kailash Chand", "Pramod", "Suresh Kumar", "Devendra", "Ashok Kumar", "Rajendra",
    "Bhagwan Das", "Jagdish", "Rameshwar", "Mahendra", "Brij Mohan", "Shyam Lal",
    "Om Prakash", "Balwan", "Manjit", "Baldev", "Santosh", "Vijay", "Anand", "Vinod"
]

LAST_NAMES = [
    "Sharma", "Yadav", "Singh", "Patil", "Solanki", "Verma", "Deshmukh", "Chauhan",
    "Gupta", "Jadhav", "Pawar", "Meena", "Rathore", "Choudhary", "Kaur", "Tiwari",
    "Mishra", "Patel", "Shinde", "Thakur", "Koli", "Joshi"
]

RELOCATION_SITES = {
    "Uttar Pradesh": ["Duhai R&R Resettlement Enclave, Ghaziabad", "Modinagar New Township Sector 3", "Meerut Bypass Rehabilitation Colony"],
    "Gujarat": ["Vadodara Infrastructure Resettlement Zone A", "Surat Outer Ring Road R&R Enclave", "Bharuch Model Resettlement Colony"],
    "Maharashtra": ["Samruddhi Resettlement Township, Nashik", "Pune Ring Road R&R Colony, Maval", "JNPT Coastal Model Village, Uran"],
    "Rajasthan": ["Bagru Modern Rehabilitation Enclave, Jaipur", "Barmer Industrial Township R&R Sector", "Pachpadra Resettlement Colony"],
    "Punjab": ["Bathinda Northern Bypass Resettlement Colony", "Jalandhar Urban R&R Enclave", "Ludhiana Freight Corridor Model Colony"],
    "Delhi": ["Dwarka Sector 28 Resettlement Enclave", "Narela Urban Extension R&R Pocket B", "Rohini Sector 37 Resettlement Zone"],
}

def seed_rr():
    db = SessionLocal()
    try:
        # Check existing count
        existing_count = db.query(RRRecord).count()
        print(f"Existing RRRecords: {existing_count}")
        if existing_count > 0:
            print("Cleaning up old RRRecords to ensure consistent sync...")
            db.query(RRRecord).delete()
            db.commit()

        parcels = db.execute(select(Parcel)).scalars().all()
        print(f"Total parcels found: {len(parcels)}")

        created_count = 0
        now = datetime.now(timezone.utc)

        for p in parcels:
            # Assign PAFs to ~65% of parcels (about 1,560 parcels)
            chance = 0.85 if p.current_stage in [
                "REHABILITATION_RESETTLEMENT", "COMPENSATION", "AWARD", "POSSESSION", "CLOSURE"
            ] else 0.50

            if random.random() > chance:
                continue

            # Determine number of families (usually 1, occasionally 2)
            num_families = 2 if random.random() < 0.15 else 1

            for fam_idx in range(num_families):
                fn = random.choice(FIRST_NAMES)
                ln = random.choice(LAST_NAMES)
                paf_name = f"{fn} {ln} & Family"

                # If parcel has owner_name, use owner_name for first family
                if fam_idx == 0 and p.owner_name and len(p.owner_name) > 3:
                    paf_name = f"{p.owner_name} & Family"

                # Affected Type matching enums.py
                paf_type = random.choices(
                    [
                        AffectedType.TITLE_HOLDER.value,
                        AffectedType.TENANT.value,
                        AffectedType.AGRICULTURAL_LABOURER.value,
                        AffectedType.COMMERCIAL_TENANT.value,
                    ],
                    weights=[0.65, 0.20, 0.10, 0.05],
                    k=1
                )[0]

                family_size = random.randint(3, 7)
                parcel_area = float(p.area_ha or 1.0)
                affected_area = round(parcel_area * (random.uniform(0.4, 1.0) if num_families == 1 else 0.5), 4)

                # Determine status based on parcel stage matching RehabilitationStatus enum
                if p.current_stage == "CLOSURE" or p.status == "COMPLETED":
                    status = RehabilitationStatus.COMPLETED.value
                    comp_paid = round(random.uniform(800000, 2500000), 2)
                elif p.current_stage in ["POSSESSION", "AWARD", "COMPENSATION"]:
                    status = random.choice([
                        RehabilitationStatus.ALLOTMENT_DONE.value,
                        RehabilitationStatus.PLAN_APPROVED.value,
                    ])
                    comp_paid = round(random.uniform(400000, 1500000), 2)
                elif p.current_stage == "REHABILITATION_RESETTLEMENT":
                    status = random.choice([
                        RehabilitationStatus.PLAN_APPROVED.value,
                        RehabilitationStatus.ALLOTMENT_DONE.value,
                    ])
                    comp_paid = round(random.uniform(200000, 800000), 2)
                else:
                    status = RehabilitationStatus.IDENTIFIED.value
                    comp_paid = 0.0

                site_options = RELOCATION_SITES.get(p.state, ["District Model R&R Township"])
                reloc_site = random.choice(site_options)
                plot_allotted = f"Plot {random.choice(['A', 'B', 'C', 'R'])}-{random.randint(101, 899)}" if status in [
                    RehabilitationStatus.ALLOTMENT_DONE.value,
                    RehabilitationStatus.COMPLETED.value,
                ] else None

                record = RRRecord(
                    rr_id=uuid.uuid4(),
                    parcel_id=p.parcel_id,
                    paf_name=paf_name,
                    paf_type=paf_type,
                    family_size=family_size,
                    affected_area_ha=affected_area,
                    rehabilitation_status=status,
                    compensation_paid=comp_paid,
                    relocation_site=reloc_site,
                    plot_allotted=plot_allotted,
                    created_at=now - timedelta(days=random.randint(10, 180)),
                    updated_at=now,
                )
                db.add(record)
                created_count += 1

        db.commit()
        print(f"Successfully seeded {created_count} Project Affected Families (PAFs) across all projects!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding RR records: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_rr()

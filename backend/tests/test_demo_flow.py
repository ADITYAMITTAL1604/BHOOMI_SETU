"""Verification script for the full 10-step BhoomiSetu Demo Story.

Walkthrough Steps:
Step 1: Open National / State Dashboard -> active projects, total land, acquisition progress, high-risk projects, SLA breaches
Step 2: Select one state -> then one project
Step 3: Open GIS map -> click a blocked/high-risk parcel
Step 4: Show parcel lifecycle and current stage
Step 5: Click "Why delayed?" -> reveal the bottleneck
Step 6: Open project intelligence -> delay-risk score with explainable contributors (SHAP)
Step 7: Show prioritized intervention cases
Step 8: Demonstrate an authorized officer update -> instant dashboard propagation
Step 9: Generate an executive MIS report (JSON and styled HTML)
Step 10: Event timeline & alerts acknowledgment
"""

from __future__ import annotations

import sys
import time
from uuid import UUID

import requests

BASE_URL = "http://localhost:8000/api/v1"


def run_demo_flow():
    print("========================================================================")
    print("  BHOOMI-SETU -- 10-STEP DEMO STORY VERIFICATION")
    print("========================================================================")

    session = requests.Session()

    # Authenticate as Central Officer (or Admin)
    print("\n[0] Authenticating demo user...")
    login_resp = session.post(
        f"{BASE_URL}/auth/login",
        data={"username": "central_user", "password": "password123"},
    )
    if login_resp.status_code != 200:
        # Try admin demo account
        login_resp = session.post(
            f"{BASE_URL}/auth/login",
            data={"username": "admin", "password": "password123"},
        )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("   [OK] Logged in successfully. Bearer token acquired.")

    # Step 1: Open National / State Dashboard
    print("\n[Step 1] Open State Dashboard (Maharashtra)...")
    r1 = session.get(f"{BASE_URL}/dashboard/state/Maharashtra")
    assert r1.status_code == 200, f"Dashboard failed: {r1.text}"
    state_dash = r1.json()
    summary = state_dash["summary"]
    print(f"   [OK] State: {state_dash['state']}")
    print(f"        Total Projects: {summary['total_projects']}")
    print(f"        Total Parcels:  {summary['total_parcels']}")
    print(f"        Land Required:  {summary['land_required_ha']} ha | Acquired: {summary['land_acquired_ha']} ha ({summary['acquisition_progress_pct']}%)")
    print(f"        SLA Breaches:   {summary['sla_breaches']}")
    assert summary["total_projects"] > 0, "Expected at least 1 project in Maharashtra"

    # Step 2: Select one state -> then one project
    print("\n[Step 2] Select a project from the list...")
    r2 = session.get(f"{BASE_URL}/projects?state=Maharashtra&page_size=5")
    assert r2.status_code == 200
    projects_data = r2.json()
    project = projects_data["items"][0]
    project_id = project["project_id"]
    project_name = project["name"]
    print(f"   [OK] Selected Project: {project_name} (ID: {project_id})")

    r2_detail = session.get(f"{BASE_URL}/projects/{project_id}")
    assert r2_detail.status_code == 200
    p_detail = r2_detail.json()
    print(f"        Type: {p_detail['type']}, Status: {p_detail['status']}")

    # Step 3: Open GIS map -> query parcels within viewport
    print("\n[Step 3] Open GIS Viewport & load project GeoJSON...")
    r3_gis = session.get(f"{BASE_URL}/gis/projects/{project_id}/geojson")
    assert r3_gis.status_code == 200
    fc = r3_gis.json()
    features = fc.get("features", [])
    print(f"   [OK] Project GeoJSON returned {len(features)} features")

    # Pick a high-risk or blocked/in-progress parcel for inspection
    selected_parcel = None
    for feat in features:
        props = feat.get("properties", {})
        if props.get("status") in ("BLOCKED", "IN_PROGRESS", "DISPUTED"):
            selected_parcel = props
            break
    if not selected_parcel and features:
        selected_parcel = features[0].get("properties", {})

    assert selected_parcel, "Expected at least 1 parcel feature"
    parcel_id = selected_parcel["parcel_id"]
    survey_no = selected_parcel["survey_number"]
    print(f"   [OK] Selected Parcel for inspection: Survey #{survey_no} (ID: {parcel_id})")

    # Step 4: Show parcel lifecycle and current stage
    print(f"\n[Step 4] Show Parcel Lifecycle for #{survey_no}...")
    r4 = session.get(f"{BASE_URL}/parcels/{parcel_id}")
    assert r4.status_code == 200
    parcel_detail = r4.json()
    stages = parcel_detail.get("stages", [])
    print(f"   [OK] Current Stage: {parcel_detail['current_stage']}, Status: {parcel_detail['status']}")
    print(f"        Owner: {parcel_detail['owner_name']}, Area: {parcel_detail['area_ha']} ha, Risk: {parcel_detail['risk_score']}")
    print(f"        Total Lifecycle Stages: {len(stages)}")

    # Step 5: Click "Why delayed?" -> reveal structured bottleneck factors
    print(f"\n[Step 5] Reveal 'Why delayed?' factors for Parcel #{survey_no}...")
    r5 = session.get(f"{BASE_URL}/analytics/parcels/{parcel_id}/why-delayed")
    assert r5.status_code == 200
    why_data = r5.json()
    print(f"   [OK] Delay Assessment: {why_data.get('overall_summary')}")
    for idx, f in enumerate(why_data.get("factors", []), 1):
        print(f"        Factor {idx} [{f.get('severity')}]: {f.get('title')} -> {f.get('explanation')[:90]}...")

    # Step 6: Open project intelligence -> delay-risk score with SHAP factors
    print(f"\n[Step 6] Project Intelligence: ML Delay-Risk Prediction for {project_name}...")
    r6 = session.get(f"{BASE_URL}/analytics/projects/{project_id}/delay-risk")
    assert r6.status_code == 200
    risk_data = r6.json()
    print(f"   [OK] Status: {risk_data.get('status')}")
    print(f"        Project Delay Risk Score: {risk_data.get('risk_score')} ({risk_data.get('risk_level')})")
    print(f"        Confidence: {risk_data.get('confidence')}")
    if risk_data.get("fallback_applied"):
        print(f"        * {risk_data.get('disclaimer')}")
    print("        Top Explainable Contributors (SHAP):")
    for factor in risk_data.get("top_factors", []):
        print(f"        - {factor.get('title')}: {factor.get('description')} (SHAP: {factor.get('shap_value')})")

    # Step 7: Show prioritized intervention cases
    print(f"\n[Step 7] Prioritized Intervention Cases for {project_name}...")
    r7 = session.get(f"{BASE_URL}/analytics/priority/{project_id}")
    assert r7.status_code == 200
    priority_data = r7.json()
    top_interventions = priority_data.get("ranked_parcels", [])[:3]
    print(f"   [OK] Total Ranked Parcels: {priority_data.get('total_ranked')}")
    for idx, p in enumerate(top_interventions, 1):
        print(f"        #{idx} Survey {p.get('survey_number')} (Score: {p.get('priority_score')}): Recommended -> {p.get('intervention_recommendation')}")

    # Step 8: Demonstrate authorized officer update -> instant dashboard propagation
    print(f"\n[Step 8] Officer Action: Update Parcel #{survey_no} status & remarks...")
    r8 = session.put(
        f"{BASE_URL}/parcels/{parcel_id}",
        json={
            "remarks": "Joint verification completed by competent authority during live inspection.",
            "status": "IN_PROGRESS",
        },
    )
    assert r8.status_code == 200, f"Update failed: {r8.text}"
    updated_parcel = r8.json()
    print(f"   [OK] Parcel updated: Status={updated_parcel['status']}, Updated at: {updated_parcel['updated_at']}")

    # Step 9: Generate an executive MIS report
    print("\n[Step 9] Generate Executive MIS Report...")
    r9_json = session.get(f"{BASE_URL}/reports/executive-summary?format=json")
    assert r9_json.status_code == 200
    r9_html = session.get(f"{BASE_URL}/reports/executive-summary?format=html")
    assert r9_html.status_code == 200
    assert "<!DOCTYPE html>" in r9_html.text
    print(f"   [OK] Executive Report generated in JSON (metrics: {list(r9_json.json().keys())[:4]}...)")
    print(f"   [OK] Styled Executive HTML Report generated ({len(r9_html.text):,} bytes)")

    # Step 10: Event Timeline & Alerts Acknowledgment
    print(f"\n[Step 10] Event Timeline & Alerts Acknowledgment...")
    r10_timeline = session.get(f"{BASE_URL}/projects/{project_id}/timeline")
    assert r10_timeline.status_code == 200
    timeline = r10_timeline.json()
    print(f"   [OK] Project Timeline: {timeline['total_events']} chronological events recorded")

    r10_alerts = session.get(f"{BASE_URL}/alerts/unread-count")
    assert r10_alerts.status_code == 200
    print(f"   [OK] Unread Alerts count: {r10_alerts.json()['unread_count']}")

    r10_read = session.put(f"{BASE_URL}/alerts/read-all")
    assert r10_read.status_code == 200
    print(f"   [OK] Marked all alerts as read: {r10_read.json()['message']}")

    print("\n========================================================================")
    print("  [SUCCESS] ALL 10 DEMO STORY STEPS COMPLETED FLAWLESSLY (0 ERRORS)!")
    print("========================================================================")


if __name__ == "__main__":
    run_demo_flow()

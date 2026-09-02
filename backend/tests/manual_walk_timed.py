"""Real-time manual walk of the 10-step demo flow with wall-clock timing."""

import time
import requests

BASE_URL = "http://localhost:8000/api/v1"

def run_timed_walk():
    overall_start = time.perf_counter()
    timings = []

    print("=" * 72)
    print("  BHOOMI-SETU -- REAL-TIME DEMO WALKTHROUGH & TIMING AUDIT")
    print("=" * 72)

    # Step 0: Login
    t0 = time.perf_counter()
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "central_user", "password": "password123"})
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    d0 = (time.perf_counter() - t0) * 1000
    timings.append(("Step 0: Officer Authentication", d0))
    print(f"[0] Login (Central User)                     -> {d0:6.1f} ms  [OK]")

    # Step 1: State Dashboard
    t1 = time.perf_counter()
    r = requests.get(f"{BASE_URL}/dashboard/state/Maharashtra", headers=headers)
    assert r.status_code == 200
    d1 = (time.perf_counter() - t1) * 1000
    timings.append(("Step 1: State Dashboard (Maharashtra)", d1))
    p_count = r.json().get('projects_count', r.json().get('total_projects', 0))
    parcels_count = r.json().get('total_parcels', 0)
    print(f"[1] State Dashboard (Maharashtra)            -> {d1:6.1f} ms  [OK] ({p_count} projects, {parcels_count} parcels)")

    # Step 2: Project List
    t2 = time.perf_counter()
    r = requests.get(f"{BASE_URL}/projects?state=Maharashtra&page_size=5", headers=headers)
    assert r.status_code == 200
    projects = r.json().get("items", r.json())
    project_id = str(projects[0]["project_id"])
    project_name = projects[0]["name"]
    d2 = (time.perf_counter() - t2) * 1000
    timings.append(("Step 2: Project Corridor Query", d2))
    print(f"[2] Project Selection ({project_name[:20]}...) -> {d2:6.1f} ms  [OK]")

    # Step 3: GIS GeoJSON Viewport
    t3 = time.perf_counter()
    r = requests.get(f"{BASE_URL}/gis/projects/{project_id}/geojson", headers=headers)
    assert r.status_code == 200
    features = r.json()["features"]
    parcel_id = features[0].get("id") or features[0]["properties"].get("parcel_id")
    survey_num = features[0]["properties"]["survey_number"]
    d3 = (time.perf_counter() - t3) * 1000
    timings.append(("Step 3: GIS GeoJSON Polygon Stream", d3))
    print(f"[3] GIS Viewport Layer ({len(features)} parcels)        -> {d3:6.1f} ms  [OK]")

    # Step 4: Parcel Lifecycle Detail
    t4 = time.perf_counter()
    r = requests.get(f"{BASE_URL}/parcels/{parcel_id}", headers=headers)
    assert r.status_code == 200
    pdata = r.json()
    d4 = (time.perf_counter() - t4) * 1000
    timings.append(("Step 4: Parcel Lifecycle Inspection", d4))
    print(f"[4] Parcel Detail (#{survey_num})               -> {d4:6.1f} ms  [OK] (Stage: {pdata['current_stage']})")

    # Step 5: Why-Delayed Root Cause
    t5 = time.perf_counter()
    r = requests.get(f"{BASE_URL}/analytics/parcels/{parcel_id}/why-delayed", headers=headers)
    assert r.status_code == 200
    wdata = r.json()
    d5 = (time.perf_counter() - t5) * 1000
    timings.append(("Step 5: Why-Delayed Root Cause Engine", d5))
    print(f"[5] 'Why Delayed?' Explainability            -> {d5:6.1f} ms  [OK] ({len(wdata.get('factors', []))} factors analyzed)")

    # Step 6: ML Delay-Risk Prediction & SHAP
    t6 = time.perf_counter()
    r = requests.get(f"{BASE_URL}/analytics/projects/{project_id}/delay-risk", headers=headers)
    assert r.status_code == 200
    mldata = r.json()
    d6 = (time.perf_counter() - t6) * 1000
    timings.append(("Step 6: XGBoost Delay-Risk & SHAP", d6))
    print(f"[6] ML Delay-Risk & SHAP Explainability      -> {d6:6.1f} ms  [OK] (Risk: {mldata.get('risk_score', 0):.3f}, Conf: {mldata.get('confidence', 0):.2f})")

    # Step 7: Priority Intervention Ranking
    t7 = time.perf_counter()
    r = requests.get(f"{BASE_URL}/analytics/priority/{project_id}", headers=headers)
    assert r.status_code == 200
    pr_data = r.json()
    d7 = (time.perf_counter() - t7) * 1000
    timings.append(("Step 7: Prioritized Intervention Queue", d7))
    print(f"[7] Priority Ranking & Recommendations      -> {d7:6.1f} ms  [OK] ({len(pr_data.get('ranked_parcels', []))} ranked cases)")

    # Step 8: Live Officer Update & Audit Ledger
    t8 = time.perf_counter()
    r = requests.put(
        f"{BASE_URL}/parcels/{parcel_id}",
        json={"status": "IN_PROGRESS", "remarks": "Live audit verification during cold-start demo."},
        headers=headers,
    )
    assert r.status_code == 200
    d8 = (time.perf_counter() - t8) * 1000
    timings.append(("Step 8: Live Status Update & Audit Ledger", d8))
    print(f"[8] Live Parcel Update & Audit Ledger        -> {d8:6.1f} ms  [OK]")

    # Step 9: Executive MIS Report
    t9 = time.perf_counter()
    r_json = requests.get(f"{BASE_URL}/reports/executive-summary?format=json", headers=headers)
    r_html = requests.get(f"{BASE_URL}/reports/executive-summary?format=html", headers=headers)
    assert r_json.status_code == 200 and r_html.status_code == 200
    d9 = (time.perf_counter() - t9) * 1000
    timings.append(("Step 9: Executive MIS Report (JSON/HTML)", d9))
    print(f"[9] Executive MIS Report (JSON + HTML)       -> {d9:6.1f} ms  [OK] (HTML size: {len(r_html.content):,} bytes)")

    # Step 10: Event Timeline & Alerts
    t10 = time.perf_counter()
    r_time = requests.get(f"{BASE_URL}/projects/{project_id}/timeline", headers=headers)
    r_unread = requests.get(f"{BASE_URL}/alerts/unread-count", headers=headers)
    r_read = requests.put(f"{BASE_URL}/alerts/read-all", headers=headers)
    assert r_time.status_code == 200 and r_unread.status_code == 200 and r_read.status_code == 200
    d10 = (time.perf_counter() - t10) * 1000
    timings.append(("Step 10: Event Timeline & Alert Lifecycle", d10))
    print(f"[10] Project Timeline & Alerts Acknowledgment -> {d10:6.1f} ms  [OK] ({len(r_time.json().get('events', []))} events)")

    total_wall_clock = time.perf_counter() - overall_start
    print("=" * 72)
    print(f"  TOTAL WALL-CLOCK TIME: {total_wall_clock:.3f} seconds ({total_wall_clock * 1000:.1f} ms)")
    print("  REQUIREMENT: Comfortably under 10 minutes (600 seconds)")
    print(f"  MARGIN: {(600.0 - total_wall_clock):.1f} seconds to spare ({total_wall_clock/600.0 * 100:.2f}% of SLA used)")
    print("=" * 72)

if __name__ == "__main__":
    run_timed_walk()

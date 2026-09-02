"""Train delay-risk XGBoost classification model and export artifacts with SHAP explainability."""

from __future__ import annotations

import json
import os
import sys
import uuid
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

# Ensure backend is in python path
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.features import FEATURE_LABELS, FEATURE_NAMES, build_features

DATA_DIR = backend_dir.parent / "data" / "ml_training"
MODEL_DIRS = [
    backend_dir / "ml" / "models",
    backend_dir.parent / "ml" / "models",
    backend_dir / "app" / "ml" / "models",
]


def generate_synthetic_training_dataset(
    projects_csv_path: Path, history_csv_path: Path, n_projects: int = 250
):
    """Generate realistic synthetic projects and multi-snapshot historical data for model training."""
    print(f"Generating synthetic training dataset ({n_projects} projects)...")
    projects_csv_path.parent.mkdir(parents=True, exist_ok=True)

    project_types = ["Highway", "Railway", "Metro", "Port", "Industrial"]
    states_pool = ["Maharashtra", "Rajasthan", "Gujarat", "Karnataka", "Tamil Nadu"]
    districts_pool = ["Pune", "Thane", "Raigad", "Jaipur", "Jodhpur", "Surat", "Vadodara"]

    projects = []
    history_rows = []

    base_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

    for i in range(n_projects):
        pid = f"PROJ-{1000 + i}"
        ptype = random.choice(project_types)
        pstate = random.choice(states_pool)
        pdistrict = random.choice(districts_pool)
        land_req = round(random.uniform(50.0, 1200.0), 2)
        total_parcels = random.randint(80, 800)

        # Assign a scenario type
        # 0: Healthy (low delay risk)
        # 1: Verification & Litigation bottleneck
        # 2: Compensation / Fund bottleneck
        # 3: District Capacity overload
        # 4: Boundary / Borderline
        scenario = random.choices([0, 1, 2, 3, 4], weights=[0.40, 0.20, 0.18, 0.12, 0.10])[0]

        if scenario == 0:
            is_delayed_30d = 0 if random.random() < 0.90 else 1
        else:
            is_delayed_30d = 1 if random.random() < 0.88 else 0

        projects.append({
            "project_id": pid,
            "name": f"{pstate} {ptype} Corridor #{i+1}",
            "type": ptype,
            "states": pstate,
            "districts": pdistrict,
            "land_required_ha": land_req,
            "land_acquired_ha": 0.0,
            "status": "ACTIVE",
            "is_delayed_30d": is_delayed_30d,
        })

        # Number of historical snapshots: 3 to 18
        n_snapshots = random.randint(3, 18)
        current_completed = 0
        current_in_progress = int(total_parcels * 0.4)
        current_blocked = random.randint(0, 5)

        total_comp_expected = land_req * random.uniform(2000000, 6000000)
        comp_paid = 0.0

        for snap_idx in range(n_snapshots):
            snap_date = base_date + timedelta(days=snap_idx * 15)

            if scenario == 0:
                # Healthy: steady processing, dropping backlog, few disputes
                new_done = random.randint(10, 35)
                current_completed = min(total_parcels, current_completed + new_done)
                current_in_progress = max(0, total_parcels - current_completed - current_blocked)
                current_blocked = max(0, current_blocked + random.randint(-2, 1))
                sla_breaches = random.randint(0, 2)
                disputes = random.randint(0, 3)
                officers = random.randint(5, 12)
                comp_paid = min(total_comp_expected, comp_paid + total_comp_expected * (0.05 * snap_idx))
                comp_pending = max(0.0, total_comp_expected * 0.3 - comp_paid * 0.2)
                stage_comp = random.uniform(0.2, 0.45)
                avg_days = random.uniform(15.0, 35.0)

            elif scenario == 1:
                # Litigation / Verification bottleneck: rising blocked parcels, surging disputes
                new_done = random.randint(1, 6)
                current_completed = min(total_parcels, current_completed + new_done)
                current_blocked = min(int(total_parcels * 0.5), current_blocked + random.randint(4, 12))
                current_in_progress = max(0, total_parcels - current_completed - current_blocked)
                sla_breaches = random.randint(4, 11)
                disputes = current_blocked + random.randint(2, 10)
                officers = random.randint(2, 5)
                comp_pending = total_comp_expected * random.uniform(0.4, 0.8)
                comp_paid = total_comp_expected * random.uniform(0.1, 0.3)
                stage_comp = random.uniform(0.75, 0.95)
                avg_days = random.uniform(65.0, 140.0)

            elif scenario == 2:
                # Compensation bottleneck: high pending funds, delayed awards
                new_done = random.randint(2, 8)
                current_completed = min(total_parcels, current_completed + new_done)
                current_blocked = min(int(total_parcels * 0.3), current_blocked + random.randint(2, 6))
                current_in_progress = max(0, total_parcels - current_completed - current_blocked)
                sla_breaches = random.randint(5, 10)
                disputes = random.randint(3, 8)
                officers = random.randint(3, 6)
                comp_pending = total_comp_expected * random.uniform(0.65, 0.92)
                comp_paid = total_comp_expected * random.uniform(0.05, 0.25)
                stage_comp = random.uniform(0.70, 0.90)
                avg_days = random.uniform(55.0, 110.0)

            elif scenario == 3:
                # Capacity deficit: very few officers, slow progress, mounting backlog
                new_done = random.randint(0, 4)
                current_completed = min(total_parcels, current_completed + new_done)
                current_in_progress = max(0, total_parcels - current_completed - current_blocked)
                current_blocked = current_blocked + random.randint(1, 4)
                sla_breaches = random.randint(6, 12)
                disputes = random.randint(2, 6)
                officers = random.choice([1, 2])
                comp_pending = total_comp_expected * random.uniform(0.5, 0.75)
                comp_paid = total_comp_expected * random.uniform(0.1, 0.3)
                stage_comp = random.uniform(0.55, 0.80)
                avg_days = random.uniform(70.0, 150.0)

            else:
                # Borderline
                new_done = random.randint(5, 15)
                current_completed = min(total_parcels, current_completed + new_done)
                current_blocked = max(0, current_blocked + random.randint(-1, 3))
                current_in_progress = max(0, total_parcels - current_completed - current_blocked)
                sla_breaches = random.randint(2, 5)
                disputes = random.randint(2, 7)
                officers = random.randint(3, 6)
                comp_pending = total_comp_expected * random.uniform(0.3, 0.6)
                comp_paid = total_comp_expected * random.uniform(0.2, 0.5)
                stage_comp = random.uniform(0.40, 0.70)
                avg_days = random.uniform(35.0, 65.0)

            history_rows.append({
                "history_id": str(uuid.uuid4()),
                "project_id": pid,
                "snapshot_date": snap_date.isoformat(),
                "land_required_ha": land_req,
                "land_acquired_ha": round(land_req * (current_completed / max(1, total_parcels)), 2),
                "parcels_total": total_parcels,
                "parcels_completed": current_completed,
                "parcels_in_progress": current_in_progress,
                "parcels_blocked": current_blocked,
                "compensation_paid_total": round(comp_paid, 2),
                "compensation_pending_total": round(comp_pending, 2),
                "stages_snapshot": json.dumps({
                    "SURVEY": int(current_in_progress * 0.3),
                    "VERIFICATION": int(current_in_progress * 0.3),
                    "OBJECTION": int(current_blocked * 0.6),
                    "AWARD": int(current_in_progress * 0.2),
                    "COMPENSATION": int(current_in_progress * 0.2),
                }),
                "metadata_json": json.dumps({
                    "officers_count": officers,
                    "sla_breaches": sla_breaches,
                    "disputes_count": disputes,
                    "avg_days_per_stage": round(avg_days, 1),
                    "stage_complexity": round(stage_comp, 4),
                }),
            })

    # Save to CSV
    df_projects = pd.DataFrame(projects)
    df_history = pd.DataFrame(history_rows)

    df_projects.to_csv(projects_csv_path, index=False)
    df_history.to_csv(history_csv_path, index=False)
    print(f"Saved {len(df_projects)} projects to {projects_csv_path}")
    print(f"Saved {len(df_history)} snapshots to {history_csv_path}")


def train_and_export():
    """Execute training pipeline, SHAP tree explainer analysis, and artifact export."""
    projects_csv = DATA_DIR / "projects.csv"
    history_csv = DATA_DIR / "project_history.csv"

    if not projects_csv.exists() or not history_csv.exists() or os.path.getsize(history_csv) == 0:
        generate_synthetic_training_dataset(projects_csv, history_csv, n_projects=260)

    print("\n1. Loading datasets...")
    df_projects = pd.read_csv(projects_csv)
    df_history = pd.read_csv(history_csv)

    print(f"Loaded {len(df_projects)} projects and {len(df_history)} snapshots.")

    # Parse JSON columns in history
    def safe_json_loads(val):
        if isinstance(val, str) and val.strip():
            try:
                return json.loads(val)
            except Exception:
                return {}
        return val if isinstance(val, dict) else {}

    df_history["stages_snapshot"] = df_history["stages_snapshot"].apply(safe_json_loads)
    df_history["metadata_json"] = df_history["metadata_json"].apply(safe_json_loads)

    print("\n2. Engineering features via shared build_features()...")
    X_rows = []
    y_labels = []

    # Group history by project_id
    history_by_project = df_history.groupby("project_id")

    for _, proj in df_projects.iterrows():
        pid = proj["project_id"]
        if pid not in history_by_project.groups:
            continue

        proj_snaps = history_by_project.get_group(pid).to_dict(orient="records")
        feats = build_features(proj_snaps, project_meta=proj.to_dict())

        X_rows.append(feats)
        y_labels.append(int(proj["is_delayed_30d"]))

    X_df = pd.DataFrame(X_rows)[FEATURE_NAMES]
    y = np.array(y_labels)

    print(f"Engineered feature matrix shape: {X_df.shape}")
    print(f"Class distribution: Delayed={np.sum(y==1)} ({np.mean(y==1)*100:.1f}%), Normal={np.sum(y==0)} ({np.mean(y==0)*100:.1f}%)")

    # 3. Stratified train/test split
    print("\n3. Performing stratified train/test split (80/20)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X_df, y, test_size=0.20, random_state=42, stratify=y
    )

    # 4. Train XGBClassifier with exact parameters
    print("\n4. Training XGBClassifier...")
    clf = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss",
    )
    clf.fit(X_train, y_train)

    # 5. Evaluate
    print("\n5. Evaluating model performance...")
    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]

    metrics = {
        "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, y_pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
    }

    print(f"   - Precision: {metrics['precision']:.4f}")
    print(f"   - Recall:    {metrics['recall']:.4f}")
    print(f"   - F1 Score:  {metrics['f1']:.4f}")
    print(f"   - ROC-AUC:   {metrics['roc_auc']:.4f}")

    # 6. SHAP TreeExplainer
    print("\n6. Initializing and testing SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(clf)
    sample_shap_values = explainer.shap_values(X_test.iloc[:5])
    print("   [OK] SHAP TreeExplainer calculated sample explanations successfully.")

    # 7. Save model and metadata
    metadata = {
        "model_name": "delay_risk_v1",
        "version": "1.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "algorithm": "XGBClassifier (n_estimators=300, max_depth=4, lr=0.05)",
        "feature_list": FEATURE_NAMES,
        "feature_labels": FEATURE_LABELS,
        "metrics": metrics,
        "risk_thresholds": {
            "low_max": 0.33,
            "medium_max": 0.66,
        },
        "training_samples": len(X_train),
        "test_samples": len(X_test),
    }

    print("\n7. Exporting artifacts...")
    for mdir in MODEL_DIRS:
        mdir.mkdir(parents=True, exist_ok=True)
        joblib.dump(clf, mdir / "delay_risk_v1.joblib")
        with open(mdir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        print(f"   [OK] Exported to {mdir}")

    print("\n" + "=" * 70)
    print("  [SUCCESS] DELAY-RISK MODEL TRAINING & EXPORT COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    train_and_export()

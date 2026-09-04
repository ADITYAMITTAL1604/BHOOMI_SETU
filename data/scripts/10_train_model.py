"""
BHOOMISETU - Script 10: Train Delay Risk Model
Trains Random Forest classifier with time-based split.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
from sklearn.impute import SimpleImputer
import joblib
from pathlib import Path

BASE_MODEL = "D:/data/model"

print("=" * 70)
print("BHOOMISETU - Script 10: Train Delay Risk Model")
print("=" * 70)

# ============================================================================
# LOAD DATA
# ============================================================================
df = pd.read_csv(f"{BASE_MODEL}/project_history_training_table.csv")
df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
print(f"✅ Loaded {len(df)} training rows")

# ============================================================================
# FEATURE SELECTION
# ============================================================================
feature_cols = [
    "pending_parcels",
    "completed_parcels",
    "average_stage_days",
    "sla_breaches",
    "compensation_pending",
    "rr_pending",
    "possession_pending",
    "processing_rate",
    "pending_trend",
    "rate_trend"
]

target_col = "elevated_risk_next_30d"

X = df[feature_cols].copy()
y = df[target_col].copy()

print(f"✅ Features: {feature_cols}")
print(f"   Target: {target_col}")
print(f"   Class balance: {y.value_counts().to_dict()}")

# ============================================================================
# TIME-BASED TRAIN/TEST SPLIT
# ============================================================================
split_date = df["snapshot_date"].quantile(0.75)
train_mask = df["snapshot_date"] <= split_date
test_mask = df["snapshot_date"] > split_date

X_train, X_test = X[train_mask], X[test_mask]
y_train, y_test = y[train_mask], y[test_mask]

print(f"\n✅ Train/Test split (time-based at {split_date.date()}):")
print(f"   Train: {len(X_train)} rows ({y_train.mean():.1%} positive)")
print(f"   Test:  {len(X_test)} rows ({y_test.mean():.1%} positive)")

# ============================================================================
# IMPUTATION (Handle 3% missing values)
# ============================================================================
imputer = SimpleImputer(strategy="median")
X_train_imputed = imputer.fit_transform(X_train)
X_test_imputed = imputer.transform(X_test)

print(f"✅ Imputed missing values (median strategy)")

# ============================================================================
# TRAIN MODEL
# ============================================================================
print("\n🔄 Training Random Forest...")
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=8,
    min_samples_leaf=10,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)
model.fit(X_train_imputed, y_train)
print("✅ Model trained!")

# ============================================================================
# EVALUATE
# ============================================================================
y_pred = model.predict(X_test_imputed)
y_prob = model.predict_proba(X_test_imputed)[:, 1]

print("\n" + "=" * 50)
print("MODEL EVALUATION")
print("=" * 50)

print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["No Risk", "Elevated Risk"]))

try:
    auc = roc_auc_score(y_test, y_prob)
    print(f"ROC AUC: {auc:.4f}")
except Exception as e:
    print(f"AUC calculation failed: {e}")
    auc = 0.0

print(f"\nConfusion Matrix:")
cm = confusion_matrix(y_test, y_pred)
print(f"  TN={cm[0][0]}  FP={cm[0][1]}")
print(f"  FN={cm[1][0]}  TP={cm[1][1]}")

# ============================================================================
# FEATURE IMPORTANCES
# ============================================================================
importances = pd.DataFrame({
    "feature": feature_cols,
    "importance": model.feature_importances_
}).sort_values("importance", ascending=False)

print("\nFeature Importances:")
for _, row in importances.iterrows():
    bar = "█" * int(row["importance"] * 50)
    print(f"  {row['feature']:25s} {row['importance']:.4f} {bar}")

importances.to_csv(f"{BASE_MODEL}/feature_importances.csv", index=False)

# ============================================================================
# SAVE MODEL & IMPUTER
# ============================================================================
joblib.dump(model, f"{BASE_MODEL}/delay_risk_model.joblib")
joblib.dump(imputer, f"{BASE_MODEL}/imputer.joblib")

print(f"\n✅ Model saved:    {BASE_MODEL}/delay_risk_model.joblib")
print(f"✅ Imputer saved:  {BASE_MODEL}/imputer.joblib")
print(f"✅ Features saved: {BASE_MODEL}/feature_importances.csv")

# ============================================================================
# EXAMPLE PREDICTION
# ============================================================================
print("\n" + "=" * 50)
print("EXAMPLE PREDICTION")
print("=" * 50)

sample = X_test.iloc[:3].copy()
sample_imputed = imputer.transform(sample)
preds = model.predict(sample_imputed)
probs = model.predict_proba(sample_imputed)[:, 1]

for i in range(len(sample)):
    risk_label = "🔴 ELEVATED" if preds[i] == 1 else "🟢 LOW"
    print(f"  Sample {i+1}: {risk_label} (probability: {probs[i]:.2%})")
    print(f"    pending={sample.iloc[i]['pending_parcels']}, rate={sample.iloc[i]['processing_rate']:.3f}, sla_breaches={sample.iloc[i]['sla_breaches']}")

# ============================================================================
# SAVE MODEL METADATA
# ============================================================================
import json
model_meta = {
    "model_type": "RandomForestClassifier",
    "n_estimators": 200,
    "max_depth": 8,
    "features": feature_cols,
    "target": target_col,
    "train_size": len(X_train),
    "test_size": len(X_test),
    "auc_score": float(auc) if auc else 0.0,
    "split_date": str(split_date.date()),
    "data_source": "synthetic"
}
with open(f"{BASE_MODEL}/model_metadata.json", "w") as f:
    json.dump(model_meta, f, indent=2)

print(f"\n✅ Model metadata saved")

print("\n" + "=" * 70)
print("✅ SCRIPT 10 COMPLETE!")
print("=" * 70)
print(f"\nAll model artifacts saved to: {BASE_MODEL}/")
print("Ready for BHOOMISETU dashboard integration!")

# BhoomiSetu — Data Repository Audit & Asset Inventory

**SIH Problem Statement**: SIH26016  
**Document Version**: 1.0 (Post-Cleanup & Production-Hardened)  
**Date**: September 2026  

---

## 1. Executive Summary

As part of the production-hardening phase of BhoomiSetu, the repository underwent a comprehensive storage and data asset audit. Over **2.3 GB** of transient caches, redundant raw shapefiles, and duplicated weight files were safely eliminated, leaving a lean, deterministic, version-controlled data directory structure.

The data layer now strictly consists of four designated directories:
- `data/model/` — Primary machine learning model and pre-processing pipeline artifacts.
- `data/processed/` — Curated feature tables and processed datasets for benchmark validation.
- `data/scripts/` — Reproducible data generation and GIS transformation scripts.
- `data/synthetic/` — Canonical synthetic ground-truth dataset matching the national land acquisition schema.

---

## 2. Retained Data Directories & Assets

### 2.1 `data/model/` (ML Serving Artifacts)
| File Name | Size | Format | Description & Role |
|:---|:---:|:---:|:---|
| `delay_risk_model.joblib` | ~1.6 MB | Joblib (scikit-learn) | Calibrated `RandomForestClassifier` trained on 10 project & stage lifecycle features to predict acquisition delay risk (low/medium/high). |
| `imputer.joblib` | ~1.2 KB | Joblib (scikit-learn) | Median imputer pre-fitted on training feature distribution to safely handle missing stage days, SLA breaches, and historical metrics in live inference. |

*Note: These artifacts are also mirrored to `backend/app/ml/models/` for standalone backend container deployment.*

### 2.2 `data/synthetic/` (Ground-Truth Enterprise Dataset)
The canonical synthetic dataset simulates 17 large-scale infrastructure projects across Uttar Pradesh, Maharashtra, and Rajasthan, encompassing 810 georeferenced land parcels.

| File | Size | Records | Description |
|:---|:---:|:---:|:---|
| `projects.csv` | 1.8 KB | 17 projects | Linear corridors, highways, transmission lines, and industrial parks with land targets. |
| `parcels_geometry.geojson` | 3.5 MB | 810 features | Valid EPSG:4326 GeoJSON polygons representing physical boundaries of affected parcels. |
| `project_parcel_links.csv` | 17.8 KB | 810 links | Relational mapping linking each parcel ID to its parent project. |
| `parcel_current_status.csv` | 71.8 KB | 810 parcels | Current stage (1-11), elapsed days, statutory SLA target, and breach flag. |
| `parcel_lifecycle_events.csv` | 432 KB | 5,200+ events | Detailed timestamped stage progression audit trail for each parcel. |
| `compensation.csv` | 32 KB | 418 records | Assessed value, approved award, solatium, and disbursement status per RFCTLARR 2013. |
| `rehabilitation_resettlement.csv` | 52 KB | 380 records | PAFs (Project Affected Families), resettlement entitlements, cash grants, and plot allotments. |
| `officers.csv` | 6.5 KB | 82 officers | Land acquisition officers, tehsildars, and grievance redressal officers with workload metrics. |
| `disputes.csv` | 12.8 KB | 147 disputes | Title objections, boundary disputes, and compensation litigation with severity classification. |
| `project_history_snapshots.csv` | 26.2 KB | 467 snapshots | Bi-weekly historical timeline snapshots capturing progress velocity and pending rates. |

### 2.3 `data/processed/` (Validation & Calibration Baselines)
- Contains normalized feature representations used for training verification and cross-validation against the ML pipeline.

### 2.4 `data/scripts/` (Pipeline Automation)
- Python scripts for synthetic parcel synthesis, geometric polygon generation, boundary projection transformations, and feature vector extraction.

---

## 3. Storage Audit & Deleted Assets (Cleanup Log)

To optimize developer onboarding, Docker build contexts, and disk storage, the following non-canonical folders were purged:
1. `data/real/` (~2.1 GB): Uncurated external OSM tile dumps, raw GIS shapefile archives, and raster DEMs that were superseded by standardized EPSG:4326 GeoJSON vector data.
2. `data/cache/` (~180 MB): Temporary joblib cache files and intermediate python run caches.
3. `data/models/` (redundant plural directory): Legacy prototype weights consolidated into `data/model/`.

**Total Space Reclaimed**: > 2.3 GB.

---

## 4. Integration Verification

1. **Model Compatibility**: `backend/app/ml/delay_risk_service.py` directly loads `delay_risk_model.joblib` and `imputer.joblib`.
2. **Feature Mapping**: Feature vector generator (`backend/app/ml/features.py`) extracts all 10 features directly from database models and `data/synthetic/officers.csv`.
3. **Database Seeder**: `backend/db/seed.py` provides automated ingestion from `data/synthetic/` into PostgreSQL/SQLite databases.

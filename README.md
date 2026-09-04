# BhoomiSetu — Real-Time National Land Acquisition & Management System

**SIH Problem Statement**: SIH26016  
**Edition**: Smart India Hackathon 2026 (SIH 2026)  
**Status**: Production-Hardened Prototype  

---

## 1. Project Overview

**BhoomiSetu** is an enterprise-grade digital platform designed for transparent, auditable, and accelerated land acquisition across national infrastructure projects (highways, railways, transmission corridors, industrial logistics hubs, and ports).

Built strictly in compliance with the **Right to Fair Compensation and Transparency in Land Acquisition, Rehabilitation and Resettlement Act (RFCTLARR), 2013**, BhoomiSetu digitizes the complete acquisition journey from proposal to project closure with real-time geospatial analytics, predictive machine learning risk forecasting, and automated statutory SLA tracking.

---

## 2. Core Architecture & Capabilities

### 2.1 The 11-Stage Statutory Workflow
BhoomiSetu models the rigorous legal progression mandated by the RFCTLARR Act:
1. `PROPOSAL` — Preliminary project corridor alignment and requirement submission.
2. `IDENTIFICATION` — Cadastral identification and affected family mapping.
3. `SURVEY` — Joint measurement survey (JMS) and geo-referencing.
4. `VERIFICATION` — Record of Rights (RoR) title verification with revenue departments.
5. `NOTIFICATION` — Section 11 preliminary notification publication.
6. `OBJECTION` — Public hearings and objection resolution under Section 15.
7. `AWARD` — Section 23/30 inquiry, valuation, and 100% solatium computation.
8. `COMPENSATION` — Direct benefit transfer and escrow tracking.
9. `REHABILITATION_RESETTLEMENT` — Resettlement scheme execution per Schedule II.
10. `POSSESSION` — Physical possession handover and police protection clearance.
11. `CLOSURE` — Land mutation, title transfer to acquiring agency, and residual audit.

### 2.2 Machine Learning Delay Risk Engine
- **Model**: Calibrated `RandomForestClassifier` trained on 10 standardized lifecycle metrics (`delay_risk_model.joblib` + `imputer.joblib`).
- **Feature Pipeline**: Dynamically extracts backlog size, SLA breach incidence, stage dwell duration, compensation backlog, and completion velocity.
- **Explainability**: Integrated tree feature-importance explainability and SHAP attribution, identifying the root causes of procedural delay with actionable mitigation guidance.

### 2.3 Interactive High-Performance GIS Engine
- Multi-polygon cadastral parcel visualization rendered via Leaflet and EPSG:4326 GeoJSON.
- Viewport-bounded spatial queries with real-time risk choropleth color-coding.
- Dynamic project filtering with zero main-thread event loop blocking.

### 2.4 Enterprise Security & Access Control
- **Role-Based Functional Access (BFLA)**: Six distinct administrative tiers (`ADMIN`, `CENTRAL`, `STATE`, `DISTRICT`, `PROJECT_AGENCY`, `FIELD_OFFICER`).
- **Geographic Scoping (BOLA)**: Strict tenancy isolation ensuring officers cannot view or mutate parcels outside their jurisdiction.
- **Mass-Assignment Defense**: Dedicated separation of standard and administrative schemas (`ParcelUpdate` vs `ParcelAdminUpdate`).
- **Cryptographic Session Defense**: Token rotation with reuse detection — replay attacks trigger immediate revocation of the compromised session family.

---

## 3. Demo User Accounts

All accounts use the standard password: `password123`

| Username | Role | Scope | Permitted Capabilities |
|:---|:---|:---|:---|
| `admin` | **ADMIN** | Global / National | Full platform control, project creation, override risk scores. |
| `central_user` | **CENTRAL** | Global / National | Cross-state macro analytics, bottlenecks, audit ledger review. |
| `state_user` | **STATE** | Maharashtra | State-level monitoring, district performance oversight. |
| `district_user` | **DISTRICT** | Pune District | Parcel record creation, award approvals, R&R reviews. |
| `agency_user` | **PROJECT_AGENCY** | Pune Projects | Infrastructure project agency liaison and milestone tracking. |
| `field_officer` | **FIELD_OFFICER** | Pune / Haveli | Field survey data submission, ground status updates. |

---

## 4. Quick Start Guide

### Option A: Docker Compose (Recommended for Production)
The system includes production-hardened Docker configurations for both backend and frontend:

```bash
# Clone and start all services
docker compose up --build -d

# Frontend: http://localhost:3000 (or http://localhost:5173 in dev)
# Backend API: http://localhost:8000/docs
```

### Option B: Local Development Setup

#### 1. Backend (FastAPI + Python 3.11)
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Seed the database from canonical synthetic datasets
python db/seed.py --reset --source synthetic

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend (React 18 + Vite + TailwindCSS)
```bash
cd frontend

# Install dependencies
npm install

# Run Vite dev server
npm run dev
```

---

## 5. Automated Verification & Testing

The repository includes a comprehensive pytest automated test suite covering security, authentication, workflow progression, and ML inference:

```bash
cd backend
python -m pytest tests/test_auth.py tests/test_security.py tests/test_workflow.py tests/test_ml.py -v
```

**Results**:
- `tests/test_auth.py` — 5 / 5 PASSED (Login, credential security, token rotation, reuse revocation).
- `tests/test_security.py` — 5 / 5 PASSED (RBAC enforcement, state/district BOLA boundaries, mass-assignment protection).
- `tests/test_workflow.py` — 2 / 2 PASSED (Sequential stage execution, audit trail logging, illegal skip prevention).
- `tests/test_ml.py` — 3 / 3 PASSED (10-feature vector schema, RandomForest inference, REST analytics endpoint).
- **Total: 15 / 15 PASSED (100%)**.

---

## 6. Project Structure

```
BHOOMI_SETU/
├── .github/
│   └── workflows/ci.yml       # Automated GitHub Actions CI pipeline
├── backend/
│   ├── app/
│   │   ├── core/              # Security, JWT, RBAC dependencies
│   │   ├── ml/                # DelayRiskService, feature extraction, models
│   │   ├── models/            # SQLAlchemy 2.0 ORM models
│   │   ├── routers/           # REST endpoints (auth, projects, parcels, gis, analytics)
│   │   └── services/          # Stage transition engine, SLA calculations
│   ├── db/
│   │   └── seed.py            # Dual-source seeder (--source synthetic | demo)
│   ├── tests/                 # Automated pytest test suite
│   └── Dockerfile             # Multi-worker production image
├── data/
│   ├── model/                 # Primary ML models (delay_risk_model.joblib, imputer.joblib)
│   ├── processed/             # Processed calibration vectors
│   ├── scripts/               # Data generation & GIS processing scripts
│   └── synthetic/             # Canonical ground-truth datasets (15 projects, 808 parcels)
├── docs/
│   ├── DATA_REPOSITORY_AUDIT.md # Data directory audit log & storage accounting
│   ├── DATA_CONTRACT.md       # Entity schemas, SLA rules, and feature contract
│   └── FINAL_IMPLEMENTATION_REPORT.md # Production hardening verification report
├── frontend/
│   ├── src/
│   │   ├── api/               # Axios client with 401 refresh queue
│   │   ├── components/        # UI components & design system
│   │   └── pages/             # Dashboard, GIS, Intelligence, Parcels, Projects
│   ├── Dockerfile             # Multi-stage build (Node 20 -> Nginx 1.25)
│   └── nginx.conf             # Production reverse-proxy & security headers
└── docker-compose.yml         # Container orchestration
```

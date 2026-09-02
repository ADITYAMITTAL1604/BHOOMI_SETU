# **BhoomiSetu — Product Requirements Document (PRD)**

**Project:** BhoomiSetu — Real-Time National Land Acquisition & Management System

**Problem Statement:** SIH26016 | Software | SIH 2026

**Version:** 1.0

**Date:** 2026-09-01

**Tagline:** *Connecting Land. Coordinating Progress. Enabling Decisions.*

────────────────────────────────────────────────────────────

## **1\. Executive Summary**

BhoomiSetu is a national land-acquisition command and decision-support platform that digitizes the entire acquisition lifecycle — from proposal to possession — into one real-time, GIS-enabled system. It uses analytics to identify bottlenecks, predict delays, prioritize intervention, and improve transparency across Central, State, District, and Project authorities.

**Core Value Proposition:** BhoomiSetu turns fragmented land-acquisition information into coordinated administrative action.

────────────────────────────────────────────────────────────

## **2\. Problem Statement**

### **2.1 The Core Problem**

Land acquisition for national infrastructure projects (highways, railways, dams, smart cities) is a multi-stage, multi-stakeholder process. Decision-makers lack a single, timely view of:

* What is happening across thousands of parcels  
* What is stuck and at which stage  
* What is likely to get delayed  
* Where intervention can unlock progress

### **2.2 Why Existing Systems Fall Short**

| Existing Ecosystem | Gap |
| :---- | :---- |
| Land records answer: Where is the land and who owns it? | They don't answer: How is acquisition progressing and what is blocking it? |
| Project systems answer: What is the project status? | They don't explain why progress is slow or where intervention is needed |
| Reports summarize what happened | They lack predictive and prioritization layers |
| Multiple sources remain fragmented | No integrated operational view exists |
| Manual coordination is required | No automated visibility, alerts, or escalation |

### **2.3 Scale of the Problem**

A single project (e.g., 100-km highway) can cross 4 states, 17 districts, and 12,000 parcels, involving survey, ownership verification, notifications, objections, compensation, rehabilitation & resettlement (R\&R), possession, and handover.

────────────────────────────────────────────────────────────

## **3\. Target Users & Personas**

| Role | Description | Primary Needs |
| :---- | :---- | :---- |
| Central Authority | Ministry / National-level decision makers | National overview, cross-state comparison, high-risk project alerts, MIS reports |
| State Authority | State-level land acquisition officers | State-wide project tracking, district comparison, bottleneck identification |
| District Authority | District collector / land acquisition officer | Parcel-level tracking, workflow management, SLA monitoring |
| Project Agency | NHAI, Railways, Smart City SPVs | Project-specific dashboards, acquisition progress, compensation tracking |
| Field Officer | Tehsildar, survey officer, revenue inspector | Parcel status updates, document uploads, stage transitions |
| System Administrator | IT admin | User management, system configuration, audit logs |

────────────────────────────────────────────────────────────

## **4\. Product Goals & Success Criteria**

### **4.1 Primary Goals**

* **End-to-end digital monitoring** of land acquisition from proposal through possession and closure  
* **Role-based access** for Central, State, District, Project, and Field stakeholders  
* **GIS-enabled** parcel and project monitoring  
* **Secure document management** with versioning and audit history  
* **Dashboards, MIS reporting, and alerts**  
* **API-ready integration** with land-record, cadastral, and other authorized government systems  
* **Predictive analytics and decision support**

### **4.2 KPIs & Success Metrics**

| Metric Area | What We Measure |
| :---- | :---- |
| Operational | Pending cases, SLA breaches, average stage duration, backlog reduction |
| AI/ML | Precision, recall, F1-score, calibration, false-positive rate |
| System | API response time (\<500ms), dashboard load time (\<3s), update propagation latency |
| Governance | Audit-trail completeness, time to identify bottleneck, time to generate reports |

────────────────────────────────────────────────────────────

## **5\. Feature Requirements**

### **5.1 P0 — Must Have (SIH Demo Critical)**

#### ***F01: Authentication & RBAC***

* JWT-based authentication  
* Role-based access control: Central, State, District, Project Agency, Field Officer, Admin  
* Geographic scope enforcement (a district officer cannot access another district's data)  
* Session management and secure logout

#### ***F02: Project Management***

* Create / edit / archive projects  
* Fields: project\_id, name, type (highway/railway/dam/smart city), states, districts, land\_required, target\_date, status  
* Project listing with filters and search  
* Project-level progress metrics

#### ***F03: Parcel Lifecycle Management***

* Create / edit parcel records linked to projects  
* Fields: parcel\_id, project\_id, survey\_number, area, geometry (GeoJSON), owner/reference, stage, status, risk\_score  
* **Acquisition workflow stages:** Proposal → Identification → Survey → Verification → Notification → Objection → Award → Compensation → R\&R → Possession → Closure  
* Stage transitions with validation rules, timestamps, and responsible officer  
* SLA timers per stage with breach detection

#### ***F04: Project Dashboard***

* Project progress: acquired area vs. required, parcel counts by stage  
* Compensation metrics: assessed, approved, paid, pending  
* R\&R metrics: affected families, rehabilitation status  
* Possession metrics: parcels possessed vs. pending  
* SLA breach summary  
* High-risk parcel count

#### ***F05: GIS Map***

* Project corridor visualization on map  
* Parcel polygons with color-coded acquisition status:  
* 🟢 GREEN \= Acquired  
* 🟡 YELLOW \= In Progress  
* 🔴 RED \= Blocked / High Risk  
* ⚪ GREY \= Not Started  
* Click parcel → owner/reference data → current stage → pending days → risk → next action  
* Village boundary overlay  
* District/state boundary layers

#### ***F06: Document Repository***

* Upload documents per project/parcel (notifications, awards, maps, reports)  
* Version control with audit history  
* Document type classification  
* Controlled access based on role

#### ***F07: National / State / District Summary Views***

* Hierarchical drill-down: National → State → District → Project → Parcel  
* Aggregated metrics at each level  
* Comparative views across states/districts

### **5.2 P1 — Should Have (Intelligence Layer)**

#### ***F08: Delay-Risk Prediction***

* ML model (XGBoost/scikit-learn) predicting probability of elevated delay in next 30 days  
* Feature inputs: days in current stage, backlog trend, processing rate, stage complexity, historical patterns  
* Confidence scores on predictions  
* Graceful degradation: "insufficient data" when history is unavailable

#### ***F09: Bottleneck Detection***

* Identify which stage is the primary bottleneck per project  
* Quantify backlog concentration (e.g., 812 of 1,438 pending parcels stuck at ownership verification)  
* "Why delayed?" explainable factor breakdown

#### ***F10: Priority Ranking & Intervention***

* Rank cases by urgency and potential impact  
* Identify cases where a single unresolved stage blocks otherwise-ready parcels  
* Intervention recommendations for authorized officers

#### ***F11: Alerts & Notifications***

* SLA breach alerts  
* Stage completion notifications  
* Escalation triggers for overdue cases  
* Role-based notification routing

### **5.3 P2 — Nice to Have**

#### ***F12: MIS Report Generation***

* Executive summary reports (PDF/Excel)  
* Project/state/district-level reports  
* Customizable date ranges and filters

#### ***F13: Configurable Workflow Templates***

* State-specific workflow stages, SLAs, roles, approval paths  
* Common national data model with configurable overlays

#### ***F14: Audit Trail***

* Full action logging: user, action, entity, timestamp, previous state, new state  
* Tamper-evident log integrity  
* Searchable audit history

────────────────────────────────────────────────────────────

## **6\. Core Data Model**

Project  
├── project\_id (PK)  
├── name, type, state, district  
├── land\_required, target\_date, status  
│  
├── Parcel (1:N)  
│   ├── parcel\_id (PK), project\_id (FK)  
│   ├── survey\_number, area, geometry (PostGIS)  
│   ├── owner/reference, stage, status, risk\_score  
│   │  
│   ├── AcquisitionStage (1:N)  
│   │   ├── stage\_id, parcel\_id, stage\_name  
│   │   ├── start\_date, target\_date, completion\_date, status  
│   │   └── assigned\_officer  
│   │  
│   ├── Compensation (1:1)  
│   │   ├── assessed\_amount, approved\_amount  
│   │   ├── paid\_amount, payment\_status  
│   │   └── payment\_date  
│   │  
│   └── Document (1:N)  
│       ├── document\_id, type, version  
│       ├── hash, uploader, timestamp  
│       └── file\_path  
│  
├── R\&R Record (1:N via parcel)  
│   ├── family/beneficiary reference  
│   ├── affected/displaced status  
│   └── rehabilitation\_status  
│  
└── AuditLog (system-wide)  
    ├── user, action, entity  
    ├── timestamp  
    └── previous\_state, new\_state

────────────────────────────────────────────────────────────

## **7\. Technology Stack**

| Layer | Technology | Rationale |
| :---- | :---- | :---- |
| Frontend | React \+ TypeScript, Tailwind CSS, shadcn/ui, Recharts, Leaflet/MapLibre | Fast development, dashboarding, GIS UI |
| Backend | Python \+ FastAPI | API-first, easy ML integration |
| Database | PostgreSQL \+ PostGIS | Relational data \+ native geospatial queries |
| ML/AI | Python, Pandas, NumPy, scikit-learn, XGBoost | Delay risk and prioritization models |
| GIS/Data | GeoPandas, Shapely | Geometry processing, geospatial analysis |
| Documents | PyMuPDF \+ OCR stack | Document upload, structured extraction |
| Auth | JWT \+ RBAC | Role-based access across admin levels |
| Deployment | Docker / Docker Compose | Reproducible hackathon deployment |

────────────────────────────────────────────────────────────

## **8\. System Architecture**

                        BHOOMISETU  
                             │  
             ┌───────────────┴───────────────┐  
             │                               │  
        WEB CLIENT                        REST APIs  
        (React \+ TS)                     (FastAPI)  
             │                               │  
             └───────────────┬───────────────┘  
                             ▼  
                     FASTAPI BACKEND  
                             │  
        ┌────────────────────┼────────────────────┐  
        ▼                    ▼                    ▼  
    Workflow             Analytics               GIS  
     Engine               Engine                Engine  
        │                    │                    │  
        └────────────────────┼────────────────────┘  
                             ▼  
                       AI / ML ENGINE  
                             │  
            ┌────────────────┼────────────────┐  
            ▼                ▼                ▼  
        Delay Risk       Bottleneck      Priority Score  
            └────────────────┼────────────────┘  
                             ▼  
                      DECISION SUPPORT  
                             │  
                             ▼  
                   PostgreSQL \+ PostGIS

────────────────────────────────────────────────────────────

## **9\. Data Strategy Summary**

### **9.1 Real Context Data**

* Department of Land Resources — DILRMP  
* LACRRIS (public reporting data)  
* Survey of India (village boundaries)  
* Bhuvan / NRSC (where permitted)  
* OpenStreetMap (road/rail corridors)  
* Public government notifications / legal documents

### **9.2 Synthetic / Prototype Data**

* 2,000–5,000 synthetic parcels for demo  
* 10–20 projects with distinct bottleneck profiles  
* Historical snapshots for ML training  
* Synthetic compensation / R\&R records  
* Synthetic workload / SLA records  
* All synthetic data explicitly labelled

### **9.3 GIS Data Requirements**

* Real administrative boundaries (state, district, village)  
* Synthetic parcel polygons inside real village polygons  
* Real road/rail corridor from OSM buffered for project footprint  
* Color-coded acquisition status overlay

────────────────────────────────────────────────────────────

## **10\. Non-Functional Requirements**

| Requirement | Target |
| :---- | :---- |
| Performance | API response \< 500ms, dashboard load \< 3s |
| Availability | Demo-stable (no production SLA) |
| Security | RBAC, JWT, encryption in transit (HTTPS), input validation |
| Scalability | Handle 5,000+ parcels with acceptable performance |
| Browser Support | Chrome, Firefox, Edge (latest versions) |
| Accessibility | Basic WCAG compliance for government use |
| Data Integrity | GeoJSON validation, lifecycle timestamp validation |

────────────────────────────────────────────────────────────

## **11\. Constraints & Assumptions**

### **Constraints**

* 4–5 day build timeline including testing  
* 6-person team (2 backend, 2 frontend, 2 research/presentation)  
* No access to real government land-acquisition data (using synthetic)  
* Prototype/demo scope — not production deployment

### **Assumptions**

* Docker-based local deployment for the hackathon  
* Synthetic data clearly labelled as such  
* AI/ML predictions are advisory, not authoritative  
* Internet connectivity available for map tile loading (with offline fallback)

────────────────────────────────────────────────────────────

## **12\. Out of Scope**

* Production deployment and cloud hosting  
* Real government system API integration (mocked with adapters)  
* Mobile native app (responsive web only)  
* Legal dispute resolution  
* Real-time streaming from live government databases  
* Multi-language/localization (English only for prototype)

────────────────────────────────────────────────────────────

## **13\. Risk Register**

| Risk | Impact | Mitigation |
| :---- | :---- | :---- |
| GIS performance with large parcel sets | Dashboard lag | Spatial indexing, viewport-based loading |
| ML model accuracy with synthetic data | Misleading predictions | Confidence scoring, "insufficient data" fallback |
| State-specific workflow complexity | Feature scope creep | Configurable templates with 1-2 demo states |
| Judge skepticism about data authenticity | Demo credibility | Clear synthetic labels, real boundary data, cited sources |
| Integration issues across team members | Build delays | Shared API contracts, daily integration builds |
| Docker environment inconsistencies | Dev friction | Pre-built Docker Compose, seed scripts |

────────────────────────────────────────────────────────────

## **14\. Demo Story (Ideal Flow)**

* Open **National Dashboard** → active projects, total land, acquisition progress, high-risk projects, SLA breaches  
* Select one **state** → then one **project**  
* Open **GIS map** → click a blocked/high-risk parcel  
* Show **parcel lifecycle** and current stage  
* Click **"Why delayed?"** → reveal the bottleneck  
* Open **project intelligence** → delay-risk score with explainable contributors  
* Show **prioritized intervention cases**  
* Demonstrate an **authorized officer update** → instant dashboard propagation  
* Generate an **executive MIS report**  
* Close: "BhoomiSetu does not only show what is delayed. It tells decision-makers why it is delayed, what is likely to happen next, and where intervention can unlock progress."

────────────────────────────────────────────────────────────

## **15\. Glossary**

| Term | Definition |
| :---- | :---- |
| Parcel | A single land plot/survey number under acquisition |
| R\&R | Rehabilitation & Resettlement |
| SLA | Service Level Agreement — target time per stage |
| RBAC | Role-Based Access Control |
| DILRMP | Digital India Land Records Modernization Programme |
| LACRRIS | Land Acquisition Cases related to RFCTLARR Act |
| PostGIS | Spatial extension for PostgreSQL |
| GeoJSON | JSON format for encoding geographic data structures |


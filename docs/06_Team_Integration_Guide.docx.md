# **BhoomiSetu — Team Integration Guide**

**Project:** BhoomiSetu | SIH26016 | SIH 2026

**Version:** 1.0

**Date:** 2026-09-01

**Purpose:** Ensure seamless integration across the 3 sub-teams working in parallel

────────────────────────────────────────────────────────────

## **1\. Team Structure & Responsibilities**

┌─────────────────────────────────────────────────────┐  
│                 BHOOMISETU TEAM (6)                  │  
│                                                     │  
│  ┌─────────────┐ ┌─────────────┐ ┌───────────────┐ │  
│  │  BACKEND    │ │  FRONTEND   │ │  RESEARCH &   │ │  
│  │  (2 devs)   │ │  (2 devs)   │ │  PRESENTATION │ │  
│  │             │ │             │ │  (2 members)  │ │  
│  │  BE-1: APIs │ │  FE-1: UI   │ │  RS-1: Data   │ │  
│  │  Auth, CRUD │ │  Dashboard  │ │  GeoJSON,     │ │  
│  │  Workflow   │ │  Charts     │ │  Synthetic    │ │  
│  │             │ │             │ │  Data Gen     │ │  
│  │  BE-2: GIS  │ │  FE-2: GIS  │ │               │ │  
│  │  Analytics  │ │  Map, Forms │ │  RS-2: ML     │ │  
│  │  ML serving │ │  Parcel Dtl │ │  Model, PPT   │ │  
│  │  Documents  │ │  Documents  │ │  Demo Prep    │ │  
│  └──────┬──────┘ └──────┬──────┘ └───────┬───────┘ │  
│         │               │                │         │  
│         └───────────────┼────────────────┘         │  
│                         ▼                           │  
│              SHARED API CONTRACTS                   │  
│              SHARED TYPE DEFINITIONS                │  
│              SHARED DATA FORMATS                    │  
└─────────────────────────────────────────────────────┘

### **1.1 Individual Role Assignments**

| Member | Role | Primary Responsibilities | Secondary |
| :---- | :---- | :---- | :---- |
| BE-1 | Backend Dev 1 | Auth/RBAC, Project CRUD, Parcel CRUD, Stage Transitions, Dashboard APIs | Docker setup, DB schema |
| BE-2 | Backend Dev 2 | GIS APIs, Analytics APIs, Document APIs, Alert APIs, ML serving | Audit log, Reports |
| FE-1 | Frontend Dev 1 | App shell, Login, Dashboard pages, Project list/detail, Charts | Theme, responsive layout |
| FE-2 | Frontend Dev 2 | GIS Map page, Parcel detail, Document upload, Analytics page, Forms | Map integration, popups |
| RS-1 | Research 1 | GeoJSON boundary sourcing, Synthetic data generator, Data validation | Corridor/parcel geometry |
| RS-2 | Research 2 | ML model training, PPT/presentation, Demo rehearsal, Judge Q\&A prep | Data source documentation |

────────────────────────────────────────────────────────────

## **2\. API Contract — The Single Source of Truth**

*⚠️ IMPORTANT:*

*The API contract is the \*\*handshake between frontend and backend\*\*. Both teams must agree on the contract BEFORE coding. Changes to the contract require a team-wide notification.*

### **2.1 Contract File Location**

bhoomisetu/  
├── docs/  
│   └── api-contracts/  
│       ├── auth.json          \# Auth endpoints request/response  
│       ├── projects.json      \# Project endpoints  
│       ├── parcels.json       \# Parcel endpoints  
│       ├── gis.json           \# GIS endpoints  
│       ├── dashboard.json     \# Dashboard endpoints  
│       ├── analytics.json     \# Analytics endpoints  
│       ├── documents.json     \# Document endpoints  
│       └── alerts.json        \# Alert endpoints

### **2.2 Contract Format (Example)**

{  
  "endpoint": "GET /api/v1/projects",  
  "description": "List projects with filters and pagination",  
  "auth": "Bearer JWT",  
  "request": {  
    "query\_params": {  
      "state": "string | optional",  
      "status": "string | optional | enum: PLANNING,ACTIVE,ON\_HOLD,COMPLETED,CANCELLED",  
      "type": "string | optional",  
      "search": "string | optional",  
      "page": "integer | default: 1",  
      "limit": "integer | default: 20 | max: 100"  
    }  
  },  
  "response\_200": {  
    "total": 47,  
    "page": 1,  
    "limit": 20,  
    "data": \[  
      {  
        "project\_id": "uuid",  
        "name": "Delhi-Meerut Infrastructure Expansion",  
        "type": "HIGHWAY",  
        "states": \["Uttar Pradesh"\],  
        "districts": \["Gautam Buddha Nagar", "Ghaziabad", "Meerut"\],  
        "land\_required\_ha": 1200.0,  
        "land\_acquired\_ha": 994.8,  
        "target\_date": "2027-03-15",  
        "status": "ACTIVE",  
        "progress\_pct": 82.9,  
        "risk\_score": 0.87,  
        "total\_parcels": 8420,  
        "acquired\_parcels": 6982,  
        "pending\_parcels": 1438,  
        "sla\_breaches": 23,  
        "created\_at": "2026-01-15T10:00:00Z",  
        "updated\_at": "2026-08-30T14:30:00Z"  
      }  
    \]  
  },  
  "response\_401": { "detail": { "code": "UNAUTHORIZED", "message": "Invalid or expired token" } },  
  "response\_403": { "detail": { "code": "FORBIDDEN", "message": "Insufficient permissions" } }  
}

### **2.3 Contract Agreement Process**

1\. BE team drafts contract → pushes to docs/api-contracts/  
2\. FE team reviews contract → requests changes if needed  
3\. Both teams agree → contract is LOCKED  
4\. Changes require:  
   a. Proposer creates a PR with updated contract  
   b. Other team reviews and approves  
   c. Both teams update their code

────────────────────────────────────────────────────────────

## **3\. Shared Type Definitions**

### **3.1 TypeScript Types (Frontend uses these directly)**

Create and maintain in frontend/src/types/api.ts:

// \============================================  
// SHARED TYPES — MUST MATCH BACKEND SCHEMAS  
// \============================================

// Enums  
export type UserRole \= 'CENTRAL' | 'STATE' | 'DISTRICT' | 'PROJECT\_AGENCY' | 'FIELD\_OFFICER' | 'ADMIN';  
export type ProjectStatus \= 'PLANNING' | 'ACTIVE' | 'ON\_HOLD' | 'COMPLETED' | 'CANCELLED';  
export type ParcelStatus \= 'NOT\_STARTED' | 'IN\_PROGRESS' | 'BLOCKED' | 'COMPLETED' | 'DISPUTED';  
export type AcquisitionStage \=   
  | 'PROPOSAL' | 'IDENTIFICATION' | 'SURVEY' | 'VERIFICATION'   
  | 'NOTIFICATION' | 'OBJECTION' | 'AWARD' | 'COMPENSATION'   
  | 'REHABILITATION\_RESETTLEMENT' | 'POSSESSION' | 'CLOSURE';  
export type AlertSeverity \= 'INFO' | 'WARNING' | 'CRITICAL';  
export type DocumentType \=   
  | 'NOTIFICATION' | 'SURVEY\_REPORT' | 'OWNERSHIP\_RECORD' | 'AWARD\_ORDER'  
  | 'COMPENSATION\_RECEIPT' | 'RR\_PLAN' | 'POSSESSION\_ORDER' | 'MAP' | 'OTHER';

// Core Models  
export interface User {  
  id: string;  
  username: string;  
  email: string;  
  role: UserRole;  
  state\_scope: string | null;  
  district\_scope: string | null;  
  is\_active: boolean;  
}

export interface Project {  
  project\_id: string;  
  name: string;  
  type: string;  
  states: string\[\];  
  districts: string\[\];  
  land\_required\_ha: number;  
  land\_acquired\_ha: number;  
  target\_date: string;  // ISO date  
  status: ProjectStatus;  
  progress\_pct: number;  
  risk\_score: number;  
  total\_parcels: number;  
  acquired\_parcels: number;  
  pending\_parcels: number;  
  sla\_breaches: number;  
  created\_at: string;  
  updated\_at: string;  
}

export interface Parcel {  
  parcel\_id: string;  
  project\_id: string;  
  survey\_number: string;  
  area\_ha: number;  
  owner\_name: string;  
  current\_stage: AcquisitionStage;  
  status: ParcelStatus;  
  risk\_score: number;  
  village: string;  
  district: string;  
  state: string;  
  days\_pending: number;  
  assigned\_officer: string | null;  
  created\_at: string;  
  updated\_at: string;  
}

export interface ParcelGeoJSON {  
  type: 'FeatureCollection';  
  features: Array\<{  
    type: 'Feature';  
    geometry: {  
      type: 'Polygon' | 'MultiPolygon';  
      coordinates: number\[\]\[\]\[\];  
    };  
    properties: Parcel;  
  }\>;  
}

export interface StageRecord {  
  stage\_id: string;  
  parcel\_id: string;  
  stage\_name: AcquisitionStage;  
  stage\_order: number;  
  start\_date: string | null;  
  target\_date: string | null;  
  completion\_date: string | null;  
  status: 'PENDING' | 'IN\_PROGRESS' | 'COMPLETED' | 'SKIPPED';  
  assigned\_officer: string | null;  
  remarks: string | null;  
}

export interface Compensation {  
  compensation\_id: string;  
  parcel\_id: string;  
  assessed\_amount: number;  
  approved\_amount: number | null;  
  paid\_amount: number | null;  
  payment\_status: 'PENDING' | 'APPROVED' | 'PAID' | 'DISPUTED';  
  payment\_date: string | null;  
}

export interface RRRecord {  
  rr\_id: string;  
  parcel\_id: string;  
  beneficiary\_name: string;  
  affected\_type: 'DISPLACED' | 'AFFECTED';  
  rehabilitation\_status: 'PENDING' | 'IN\_PROGRESS' | 'COMPLETED';  
  entitlements: string;  
}

// Dashboard  
export interface NationalDashboard {  
  active\_projects: number;  
  total\_land\_ha: number;  
  acquired\_pct: number;  
  sla\_breaches: number;  
  stage\_distribution: Record\<AcquisitionStage, number\>;  
  compensation\_summary: {  
    assessed: number;  
    approved: number;  
    paid: number;  
  };  
  state\_summary: Array\<{  
    state: string;  
    projects: number;  
    land\_ha: number;  
    acquired\_pct: number;  
    risk\_level: 'LOW' | 'MEDIUM' | 'HIGH';  
    sla\_breaches: number;  
  }\>;  
  high\_risk\_projects: Project\[\];  
}

// Analytics  
export interface DelayRiskResult {  
  project\_id: string;  
  risk\_score: number;    // 0.0 \- 1.0  
  risk\_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';  
  confidence: number;    // 0.0 \- 1.0  
  snapshots\_used: number;  
  insufficient\_data: boolean;  
  feature\_importance: Array\<{  
    feature: string;  
    label: string;         // Human-readable  
    importance: number;    // SHAP value  
    direction: 'positive' | 'negative';  
  }\>;  
}

export interface BottleneckResult {  
  project\_id: string;  
  primary\_bottleneck: {  
    stage: AcquisitionStage;  
    pending\_count: number;  
    avg\_days\_pending: number;  
    sla\_days: number;  
    breach\_rate: number;  
    impact\_description: string;  
  };  
  all\_stages: Array\<{  
    stage: AcquisitionStage;  
    pending\_count: number;  
    avg\_days\_pending: number;  
    bottleneck\_score: number;  
  }\>;  
}

export interface PriorityCase {  
  parcel\_id: string;  
  survey\_number: string;  
  stage: AcquisitionStage;  
  days\_pending: number;  
  impact: 'LOW' | 'MEDIUM' | 'HIGH';  
  priority\_score: number;  
  recommendation: string;  
}

export interface WhyDelayed {  
  parcel\_id: string;  
  factors: Array\<{  
    factor: string;  
    description: string;  
    weight: number;  // 0.0 \- 1.0  
  }\>;  
  summary: string;  
}

// Pagination  
export interface PaginatedResponse\<T\> {  
  total: number;  
  page: number;  
  limit: number;  
  data: T\[\];  
}

// Auth  
export interface LoginRequest {  
  username: string;  
  password: string;  
}

export interface LoginResponse {  
  access\_token: string;  
  refresh\_token: string;  
  token\_type: 'bearer';  
  user: User;  
}

// API Error  
export interface ApiError {  
  detail: {  
    code: string;  
    message: string;  
    timestamp: string;  
  };  
}

### **3.2 Backend Pydantic Schemas (Must Match TypeScript)**

\# backend/app/schemas/project.py  
class ProjectResponse(BaseModel):  
    project\_id: UUID  
    name: str  
    type: str  
    states: list\[str\]  
    districts: list\[str\]  
    land\_required\_ha: float  
    land\_acquired\_ha: float  
    target\_date: date  
    status: ProjectStatus  
    progress\_pct: float  
    risk\_score: float  
    total\_parcels: int  
    acquired\_parcels: int  
    pending\_parcels: int  
    sla\_breaches: int  
    created\_at: datetime  
    updated\_at: datetime

*🔴 CAUTION:*

*\*\*Field name mismatches\*\* are the \#1 integration bug. Use \`snake\_case\` everywhere (both Python and TypeScript). Do NOT use camelCase in API responses.*

────────────────────────────────────────────────────────────

## **4\. Data Format Agreements**

### **4.1 Date/Time Format**

* **Always ISO 8601:** 2026-09-01T12:30:00Z  
* **Date only:** 2026-09-01  
* **Timezone:** UTC in API, convert to IST in frontend display

### **4.2 GeoJSON Format**

* **SRID:** 4326 (WGS 84\)  
* **Structure:** Standard GeoJSON FeatureCollection  
* **Properties:** Include full parcel data in properties (not just ID)

{  
  "type": "FeatureCollection",  
  "features": \[  
    {  
      "type": "Feature",  
      "geometry": {  
        "type": "Polygon",  
        "coordinates": \[\[\[77.31, 28.57\], \[77.32, 28.57\], \[77.32, 28.58\], \[77.31, 28.58\], \[77.31, 28.57\]\]\]  
      },  
      "properties": {  
        "parcel\_id": "uuid",  
        "survey\_number": "102/A",  
        "current\_stage": "VERIFICATION",  
        "status": "IN\_PROGRESS",  
        "risk\_score": 0.73,  
        "days\_pending": 45  
      }  
    }  
  \]  
}

### **4.3 Currency Format**

* **API:** Raw numbers (float/decimal) in INR  
* **Frontend display:** Format with ₹ symbol, lakhs/crores notation  
* 1234567.89 → ₹12.35L or ₹12,34,567.89

### **4.4 Pagination Format**

{  
  "total": 8420,  
  "page": 1,  
  "limit": 20,  
  "data": \[...\]  
}

* Frontend sends: ?page=1\&limit=20  
* Backend returns: consistent pagination envelope

### **4.5 Error Format**

{  
  "detail": {  
    "code": "PARCEL\_NOT\_FOUND",  
    "message": "Parcel with ID xyz not found",  
    "timestamp": "2026-09-01T12:00:00Z"  
  }  
}

────────────────────────────────────────────────────────────

## **5\. Development Workflow & Git Strategy**

### **5.1 Branching Strategy**

main (protected — deploy/demo ready)  
  │  
  ├── develop (integration branch — daily merges)  
  │     │  
  │     ├── feature/be-auth           (BE-1)  
  │     ├── feature/be-project-crud   (BE-1)  
  │     ├── feature/be-gis-apis       (BE-2)  
  │     ├── feature/be-analytics      (BE-2)  
  │     │  
  │     ├── feature/fe-app-shell      (FE-1)  
  │     ├── feature/fe-dashboard      (FE-1)  
  │     ├── feature/fe-gis-map        (FE-2)  
  │     ├── feature/fe-parcel-detail  (FE-2)  
  │     │  
  │     ├── feature/data-boundaries   (RS-1)  
  │     ├── feature/data-synthetic    (RS-1)  
  │     └── feature/ml-delay-model    (RS-2)  
  │  
  └── hotfix/\* (critical fixes during testing)

### **5.2 Merge Rules**

| Rule | Detail |
| :---- | :---- |
| PR required for develop and main | No direct pushes |
| At least 1 reviewer | Cross-team preferred |
| CI must pass | Backend tests \+ frontend build |
| Merge to develop | Daily at end of day (minimum) |
| Merge to main | Only when all tests pass (Day 3-4) |
| Conflict resolution | Resolved by the later PR author |

### **5.3 Commit Convention**

feat: add project CRUD APIs  
fix: scope filter not applied to parcel query  
docs: update API contract for analytics  
data: add synthetic parcel generator  
test: add auth scope enforcement tests  
chore: update Docker compose config

────────────────────────────────────────────────────────────

## **6\. Mock Data & Parallel Development**

### **6.1 Frontend Mock Server**

Until backend APIs are ready, frontend uses **mock JSON** files:

frontend/src/mocks/  
├── projects.json         \# 5 sample projects  
├── parcels.json          \# 20 sample parcels  
├── dashboard.json        \# Dashboard metrics  
├── analytics.json        \# Risk/bottleneck data  
├── geojson-parcels.json  \# Sample GeoJSON  
└── mock-server.ts        \# Intercepts API calls in dev

**Pattern:**

// api/projects.ts  
export async function listProjects(filters: ProjectFilters) {  
  if (import.meta.env.DEV && import.meta.env.VITE\_USE\_MOCKS \=== 'true') {  
    const { default: mockData } \= await import('../mocks/projects.json');  
    return mockData;  
  }  
  return apiClient.get('/projects', { params: filters });  
}

*💡 TIP:*

*FE team should create mocks on \*\*Day 1 morning\*\* based on API contracts, enabling parallel development from Day 1 itself.*

### **6.2 Backend Standalone Testing**

Backend team tests APIs independently using:

* **pytest** with test database  
* **Swagger UI** (/docs) for manual testing  
* **curl / httpie** for quick checks

### **6.3 Research Team Data Handoff**

Research generates → commits to data/ directory → Backend loads into DB

data/  
├── boundaries/  
│   ├── india\_states.geojson       (RS-1 generates, BE-2 loads)  
│   ├── up\_districts.geojson       (RS-1 generates, BE-2 loads)  
│   └── demo\_villages.geojson      (RS-1 generates, BE-2 loads)  
├── synthetic/  
│   ├── projects.csv               (RS-1 generates, BE-1 loads via seed)  
│   ├── parcels.csv                (RS-1 generates, BE-1 loads via seed)  
│   ├── parcel\_geometries.geojson  (RS-1 generates, BE-2 loads)  
│   ├── stages.csv                 (RS-1 generates, BE-1 loads via seed)  
│   ├── compensation.csv           (RS-1 generates, BE-1 loads via seed)  
│   ├── rr\_records.csv             (RS-1 generates, BE-1 loads via seed)  
│   └── project\_history.csv        (RS-1 generates, RS-2 uses for ML)  
└── ml/  
    ├── models/  
    │   └── delay\_risk\_v1.joblib   (RS-2 trains, BE-2 serves)  
    └── metadata.json              (RS-2 creates, BE-2 reads)

────────────────────────────────────────────────────────────

## **7\. Integration Checkpoints (Daily Syncs)**

### **Day 1 — End of Day**

| Checkpoint | Owner | Validator |
| :---- | :---- | :---- |
| Docker Compose starts all 3 services | BE-1 | All |
| DB schema created, migrations work | BE-1 | BE-2 |
| Auth API works (login/logout/refresh) | BE-1 | FE-1 |
| Login page connects to real auth API | FE-1 | BE-1 |
| App shell (sidebar, routing) renders | FE-1 | FE-2 |
| Project CRUD API returns data | BE-1 | FE-1 |
| Project list page renders (with mocks or real API) | FE-1 | BE-1 |
| Real admin boundaries (3-5 districts) committed | RS-1 | BE-2 |
| Synthetic data generator first draft running | RS-1 | BE-1 |

**Integration test:** Login → see project list → logout

### **Day 2 — End of Day**

| Checkpoint | Owner | Validator |
| :---- | :---- | :---- |
| GIS APIs return valid GeoJSON | BE-2 | FE-2 |
| Map page shows real parcel polygons | FE-2 | BE-2 |
| Dashboard API returns correct metrics | BE-1 | FE-1 |
| National dashboard renders with real data | FE-1 | BE-1 |
| Parcel CRUD \+ stage transition API works | BE-1 | FE-2 |
| Parcel detail page renders with real data | FE-2 | BE-1 |
| Document upload/download API works | BE-2 | FE-2 |
| Synthetic dataset (2000+ parcels) loaded | RS-1 | BE-1 |
| ML training dataset prepared | RS-1 | RS-2 |

**Integration test:** Login → dashboard → click project → view map → click parcel → transition stage → see dashboard update

### **Day 3 — End of Day**

| Checkpoint | Owner | Validator |
| :---- | :---- | :---- |
| Analytics APIs (bottleneck, risk, priority) work | BE-2 | FE-2 |
| Analytics page renders with real predictions | FE-2 | BE-2 |
| ML model trained and served via API | RS-2 \+ BE-2 | FE-2 |
| Alert system works (SLA breach triggers) | BE-2 | FE-1 |
| State/district dashboards work | FE-1 \+ BE-1 | All |
| "Why delayed?" works end-to-end | BE-2 \+ FE-2 | RS-2 |
| All 10 demo story steps work | All | RS-2 |

**Integration test:** Full demo story walkthrough (all 10 steps)

### **Day 4 — End of Day (Testing)**

| Checkpoint | Owner | Validator |
| :---- | :---- | :---- |
| All security tests pass | BE | FE |
| All scope/auth tests pass | BE | FE |
| All GIS validation tests pass | BE \+ RS | FE |
| All ML edge cases handled | RS \+ BE | FE |
| End-to-end demo flow stable | All | All |
| Demo dataset locked | RS-1 | All |
| No critical bugs remaining | All | All |

### **Day 5 — End of Day (Polish)**

| Checkpoint | Owner | Validator |
| :---- | :---- | :---- |
| All Day 4 bugs fixed | All | All |
| UX polished (loading states, empty states, errors) | FE | All |
| Presentation ready | RS-2 | All |
| Demo rehearsed (2+ dry runs) | All | All |
| Backup dataset \+ environment ready | RS-1 \+ BE-1 | All |

────────────────────────────────────────────────────────────

## **8\. Environment Setup — First Hour of Day 1**

### **8.1 Prerequisites (everyone)**

\# Required tools  
git \--version          \# 2.40+  
docker \--version       \# 24+  
docker-compose \--version  \# 2.20+  
node \--version         \# 18+  
python \--version       \# 3.11+

### **8.2 Setup Script**

\# Clone  
git clone \<repo-url\> bhoomisetu  
cd bhoomisetu

\# Start everything  
docker-compose up \-d

\# Verify  
curl http://localhost:8000/docs        \# FastAPI Swagger  
curl http://localhost:3000             \# React app  
psql postgresql://bhoomisetu:password@localhost:5432/bhoomisetu \-c "SELECT PostGIS\_Version();"

\# Seed data (once RS-1 has generated it)  
docker exec bhoomisetu-backend python db/seed.py

### **8.3 Shared Environment Variables**

\# .env (shared, committed as .env.example)  
DATABASE\_URL=postgresql+asyncpg://bhoomisetu:bhoomisetu\_dev@db:5432/bhoomisetu  
JWT\_SECRET=dev-secret-change-in-production-xxxxxxxxxxxxxxxx  
JWT\_ALGORITHM=HS256  
JWT\_EXPIRY\_MINUTES=60  
CORS\_ORIGINS=http://localhost:3000  
DOCUMENT\_STORAGE\_PATH=/app/documents  
ML\_MODEL\_PATH=/app/ml/models  
VITE\_API\_BASE\_URL=http://localhost:8000/api/v1  
VITE\_MAP\_TILE\_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png  
VITE\_USE\_MOCKS=false

────────────────────────────────────────────────────────────

## **9\. Communication Protocol**

### **9.1 Sync Schedule**

| When | What | Duration | Who |
| :---- | :---- | :---- | :---- |
| Day start (9:00 AM) | Standup: what I did, what I'll do, blockers | 10 min | All 6 |
| Mid-day (2:00 PM) | Integration check: merge, test, report issues | 15 min | All 6 |
| End of day (8:00 PM) | Integration merge \+ demo of day's progress | 20 min | All 6 |
| Ad-hoc | Pair on blockers | As needed | 2-3 people |

### **9.2 Blocker Escalation**

1\. Try to solve independently (15 min)  
2\. Ping your sub-team partner  
3\. If cross-team dependency → message the other team immediately  
4\. If \> 30 min blocked → escalate to full team

### **9.3 Contract Change Protocol**

Proposer → Message in team chat:  
  "⚠️ API CONTRACT CHANGE: \[endpoint\] — \[description of change\]"

Other team acknowledges within 30 minutes.

Change is committed to docs/api-contracts/ with the code change.

────────────────────────────────────────────────────────────

## **10\. Merge Conflict Prevention**

### **10.1 File Ownership**

| Directory | Primary Owner | Others May Edit? |
| :---- | :---- | :---- |
| backend/app/routers/auth.py | BE-1 | No |
| backend/app/routers/projects.py | BE-1 | No |
| backend/app/routers/parcels.py | BE-1 | No |
| backend/app/routers/gis.py | BE-2 | No |
| backend/app/routers/analytics.py | BE-2 | No |
| backend/app/routers/documents.py | BE-2 | No |
| backend/app/models/ | BE-1 (schema) | BE-2 (additions only) |
| backend/app/middleware/ | BE-1 | No |
| frontend/src/pages/LoginPage.tsx | FE-1 | No |
| frontend/src/pages/DashboardPage.tsx | FE-1 | No |
| frontend/src/pages/ProjectListPage.tsx | FE-1 | No |
| frontend/src/pages/GISMapPage.tsx | FE-2 | No |
| frontend/src/pages/ParcelDetailPage.tsx | FE-2 | No |
| frontend/src/pages/AnalyticsPage.tsx | FE-2 | No |
| frontend/src/components/layout/ | FE-1 | FE-2 (nav items) |
| frontend/src/types/api.ts | FE-1 | FE-2 (additions) |
| frontend/src/api/ | FE-1 (base) | FE-2 (new files) |
| data/ | RS-1 | RS-2 (ml/ only) |
| backend/app/ml/ | RS-2 \+ BE-2 | Coordinate |
| docker-compose.yml | BE-1 | Coordinate changes |

### **10.2 Shared File Rules**

Files that **multiple people** might edit:

| File | Rule |
| :---- | :---- |
| docker-compose.yml | Only BE-1 edits. Others request via message. |
| backend/requirements.txt | Add new deps in your branch; merge resolves alphabetically. |
| frontend/package.json | Add new deps in your branch; merge resolves. |
| frontend/src/App.tsx | FE-1 owns routing; FE-2 adds route entries only. |
| frontend/src/types/api.ts | FE-1 owns; FE-2 adds new types at bottom. |
| README.md | RS-2 owns; others suggest via PR comments. |

────────────────────────────────────────────────────────────

## **11\. Integration Testing Checklist**

### **11.1 Cross-Team Integration Tests**

| \# | Test | BE | FE | RS | Status |
| :---- | :---- | :---- | :---- | :---- | :---- |
| INT-01 | Login flow: FE sends credentials → BE validates → FE stores token → redirects | ✅ | ✅ | ☐ |  |
| INT-02 | Protected route: FE attaches JWT → BE validates → returns scoped data | ✅ | ✅ | ☐ |  |
| INT-03 | Project list: FE requests → BE returns paginated data → FE renders table | ✅ | ✅ | ☐ |  |
| INT-04 | GIS map: FE requests GeoJSON → BE returns → FE renders parcel polygons | ✅ | ✅ | ☐ |  |
| INT-05 | Parcel popup: FE clicks polygon → reads properties → displays popup | ✅ | ✅ | ☐ |  |
| INT-06 | Stage transition: FE sends transition → BE validates → updates DB → FE refreshes | ✅ | ✅ | ☐ |  |
| INT-07 | Dashboard metrics: BE computes from DB → FE renders charts | ✅ | ✅ | ☐ |  |
| INT-08 | Synthetic data: RS generates → BE seeds DB → FE shows in dashboard | ✅ | ✅ | ✅ | ☐ |
| INT-09 | ML prediction: RS model loaded by BE → FE requests risk → displays score | ✅ | ✅ | ✅ | ☐ |
| INT-10 | Document upload: FE sends file → BE stores → FE lists documents | ✅ | ✅ | ☐ |  |
| INT-11 | Scope enforcement: FE logged as district → BE returns only district data → FE shows only district | ✅ | ✅ | ☐ |  |
| INT-12 | Demo flow: All 10 steps work end-to-end | ✅ | ✅ | ✅ | ☐ |

### **11.2 Data Flow Validation**

RS-1 generates boundaries →   
  BE-2 loads into PostGIS →   
    FE-2 renders on map →   
      ✅ Boundaries match real geography

RS-1 generates parcels →   
  BE-1 seeds into DB →   
    BE-1 computes dashboard metrics →   
      FE-1 renders dashboard →   
        ✅ Numbers are consistent

RS-1 generates project\_history →   
  RS-2 trains ML model →   
    BE-2 serves predictions →   
      FE-2 renders analytics page →   
        ✅ Risk scores make sense

RS-1 generates parcel geometry →   
  BE-2 serves as GeoJSON →   
    FE-2 renders on map →   
      FE-2 clicks parcel → popup shows correct data →   
        FE-2 navigates to parcel detail →   
          ✅ Data is consistent across map and detail page

────────────────────────────────────────────────────────────

## **12\. Troubleshooting Common Integration Issues**

| Issue | Cause | Fix |
| :---- | :---- | :---- |
| CORS error in browser | Backend CORS not configured for frontend URL | Check CORS\_ORIGINS in .env |
| 401 on all requests | JWT secret mismatch or token expired | Ensure same JWT\_SECRET in backend .env |
| Empty dashboard | Seed data not loaded | Run python db/seed.py in backend container |
| Map shows no parcels | GeoJSON format mismatch | Verify FeatureCollection structure matches contract |
| Wrong data types | Python returns date, TS expects string | Ensure JSON serialization uses ISO strings |
| Pagination mismatch | Different page numbering (0-based vs 1-based) | Standardize on 1-based |
| DB connection refused | Backend can't reach PostgreSQL | Check Docker network; use db as hostname |
| PostGIS not available | Extension not created | Run CREATE EXTENSION postgis; in init.sql |
| ML model file not found | Model path mismatch | Check ML\_MODEL\_PATH and volume mount |
| Geometry render fail | Invalid GeoJSON coordinates | Validate with ST\_IsValid before serving |


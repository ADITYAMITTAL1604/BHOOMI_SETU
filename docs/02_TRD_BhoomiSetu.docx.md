# **BhoomiSetu — Technical Requirements Document (TRD)**

**Project:** BhoomiSetu — Real-Time National Land Acquisition & Management System

**Problem Statement:** SIH26016 | SIH 2026

**Version:** 1.0

**Date:** 2026-09-01

────────────────────────────────────────────────────────────

## **1\. System Architecture Overview**

┌──────────────────────────────────────────────────────────┐  
│                      CLIENT TIER                         │  
│  React 18 \+ TypeScript \+ Vite                            │  
│  ┌────────┐ ┌──────────┐ ┌─────────┐ ┌───────────────┐  │  
│  │shadcn/ │ │ Recharts │ │Leaflet/ │ │  React Query  │  │  
│  │  ui    │ │          │ │MapLibre │ │  / TanStack    │  │  
│  └────────┘ └──────────┘ └─────────┘ └───────────────┘  │  
└──────────────────────┬───────────────────────────────────┘  
                       │ HTTPS / REST JSON  
┌──────────────────────▼───────────────────────────────────┐  
│                    API GATEWAY                           │  
│  FastAPI  │  JWT Auth Middleware  │  CORS  │  Rate Limit │  
└──────────────────────┬───────────────────────────────────┘  
                       │  
┌──────────────────────▼───────────────────────────────────┐  
│                  APPLICATION TIER                         │  
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐    │  
│  │  Workflow     │ │   GIS Engine  │ │  Analytics   │    │  
│  │  Engine       │ │  (GeoPandas,  │ │  Engine      │    │  
│  │  (State       │ │   Shapely,    │ │  (Pandas,    │    │  
│  │  Machine)     │ │   PostGIS)    │ │  NumPy)      │    │  
│  └──────────────┘ └───────────────┘ └──────────────┘    │  
│  ┌──────────────┐ ┌───────────────┐ ┌──────────────┐    │  
│  │  ML Engine   │ │  Document     │ │  Notification│    │  
│  │  (scikit,    │ │  Manager      │ │  Service     │    │  
│  │  XGBoost)    │ │  (PyMuPDF)    │ │              │    │  
│  └──────────────┘ └───────────────┘ └──────────────┘    │  
└──────────────────────┬───────────────────────────────────┘  
                       │  
┌──────────────────────▼───────────────────────────────────┐  
│                     DATA TIER                            │  
│  ┌──────────────────────┐  ┌──────────────────────────┐  │  
│  │  PostgreSQL 16       │  │  File Storage            │  │  
│  │  \+ PostGIS 3.4       │  │  (Local / S3-compatible) │  │  
│  │                      │  │                          │  │  
│  │  Tables: 12+         │  │  Documents, GeoJSON,     │  │  
│  │  Spatial Indexes     │  │  ML model artifacts      │  │  
│  └──────────────────────┘  └──────────────────────────┘  │  
└──────────────────────────────────────────────────────────┘

────────────────────────────────────────────────────────────

## **2\. Technology Stack — Detailed Specifications**

### **2.1 Frontend**

| Component | Version | Purpose |
| :---- | :---- | :---- |
| React | 18.x | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | 5.x | Build tool / dev server |
| Tailwind CSS | 3.x | Utility-first styling |
| shadcn/ui | latest | Pre-built accessible components |
| Recharts | 2.x | Dashboard charts (bar, line, pie, area) |
| Leaflet / MapLibre GL | 1.9.x / 4.x | GIS map rendering |
| React Query (TanStack) | 5.x | Server state management, caching |
| React Router | 6.x | Client-side routing |
| Zustand | 4.x | Client state management |
| Axios | 1.x | HTTP client |
| React Hook Form \+ Zod | latest | Form handling \+ validation |

### **2.2 Backend**

| Component | Version | Purpose |
| :---- | :---- | :---- |
| Python | 3.11+ | Runtime |
| FastAPI | 0.110+ | REST API framework |
| Uvicorn | latest | ASGI server |
| SQLAlchemy | 2.x | ORM |
| GeoAlchemy2 | 0.14+ | PostGIS ORM integration |
| Alembic | 1.x | Database migrations |
| Pydantic | 2.x | Request/response validation |
| python-jose / PyJWT | latest | JWT token handling |
| passlib \+ bcrypt | latest | Password hashing |
| GeoPandas | 0.14+ | Geospatial data processing |
| Shapely | 2.x | Geometry operations |
| Pandas / NumPy | latest | Data manipulation |
| scikit-learn | 1.4+ | ML models |
| XGBoost | 2.x | Gradient boosting for delay-risk |
| PyMuPDF (fitz) | latest | PDF document processing |
| python-multipart | latest | File uploads |

### **2.3 Database**

| Component | Version | Purpose |
| :---- | :---- | :---- |
| PostgreSQL | 16.x | Primary RDBMS |
| PostGIS | 3.4+ | Spatial queries, geometry storage |

### **2.4 DevOps**

| Component | Purpose |
| :---- | :---- |
| Docker \+ Docker Compose | Containerized deployment |
| Git \+ GitHub | Version control |
| pytest | Backend testing |
| Vitest / Jest | Frontend testing |

────────────────────────────────────────────────────────────

## **3\. Database Schema**

### **3.1 Entity-Relationship Diagram**

erDiagram  
    USERS ||--o{ AUDIT\_LOG : creates  
    USERS {  
        uuid id PK  
        string username UK  
        string email UK  
        string password\_hash  
        string role  
        string state\_scope  
        string district\_scope  
        boolean is\_active  
        timestamp created\_at  
    }  
      
    PROJECT ||--|{ PARCEL : contains  
    PROJECT {  
        uuid project\_id PK  
        string name  
        string type  
        string\[\] states  
        string\[\] districts  
        float land\_required\_ha  
        float land\_acquired\_ha  
        date target\_date  
        string status  
        geometry corridor\_geometry  
        uuid created\_by FK  
        timestamp created\_at  
        timestamp updated\_at  
    }  
      
    PARCEL ||--|{ ACQUISITION\_STAGE : has  
    PARCEL ||--o| COMPENSATION : has  
    PARCEL ||--o{ DOCUMENT : has  
    PARCEL ||--o{ RR\_RECORD : has  
    PARCEL {  
        uuid parcel\_id PK  
        uuid project\_id FK  
        string survey\_number  
        float area\_ha  
        geometry geometry  
        string owner\_name  
        string owner\_reference  
        string current\_stage  
        string status  
        float risk\_score  
        string village  
        string district  
        string state  
        uuid assigned\_officer FK  
        timestamp created\_at  
        timestamp updated\_at  
    }  
      
    ACQUISITION\_STAGE {  
        uuid stage\_id PK  
        uuid parcel\_id FK  
        string stage\_name  
        int stage\_order  
        date start\_date  
        date target\_date  
        date completion\_date  
        string status  
        uuid assigned\_officer FK  
        text remarks  
        timestamp created\_at  
    }  
      
    COMPENSATION {  
        uuid compensation\_id PK  
        uuid parcel\_id FK  
        decimal assessed\_amount  
        decimal approved\_amount  
        decimal paid\_amount  
        string payment\_status  
        date payment\_date  
        text remarks  
    }  
      
    RR\_RECORD {  
        uuid rr\_id PK  
        uuid parcel\_id FK  
        string beneficiary\_name  
        string beneficiary\_reference  
        string affected\_type  
        string rehabilitation\_status  
        text entitlements  
        timestamp updated\_at  
    }  
      
    DOCUMENT {  
        uuid document\_id PK  
        uuid entity\_id FK  
        string entity\_type  
        string document\_type  
        string filename  
        string file\_path  
        string file\_hash  
        int version  
        uuid uploaded\_by FK  
        timestamp uploaded\_at  
    }  
      
    AUDIT\_LOG {  
        uuid log\_id PK  
        uuid user\_id FK  
        string action  
        string entity\_type  
        uuid entity\_id  
        jsonb previous\_state  
        jsonb new\_state  
        string ip\_address  
        timestamp created\_at  
    }  
      
    PROJECT\_HISTORY {  
        uuid history\_id PK  
        uuid project\_id FK  
        date snapshot\_date  
        int total\_parcels  
        int pending\_parcels  
        int acquired\_parcels  
        float processing\_rate  
        float backlog\_trend  
        float risk\_score  
        jsonb stage\_distribution  
    }  
      
    WORKFLOW\_TEMPLATE {  
        uuid template\_id PK  
        string name  
        string state  
        string programme\_type  
        jsonb stages  
        jsonb sla\_config  
        jsonb role\_mapping  
        boolean is\_default  
    }  
      
    ALERT {  
        uuid alert\_id PK  
        uuid user\_id FK  
        string alert\_type  
        string severity  
        uuid entity\_id  
        string entity\_type  
        string message  
        boolean is\_read  
        timestamp created\_at  
    }

### **3.2 Key Indexes**

\-- Spatial indexes  
CREATE INDEX idx\_parcel\_geometry ON parcel USING GIST (geometry);  
CREATE INDEX idx\_project\_corridor ON project USING GIST (corridor\_geometry);

\-- Query performance indexes  
CREATE INDEX idx\_parcel\_project ON parcel (project\_id);  
CREATE INDEX idx\_parcel\_stage ON parcel (current\_stage);  
CREATE INDEX idx\_parcel\_status ON parcel (status);  
CREATE INDEX idx\_parcel\_state\_district ON parcel (state, district);  
CREATE INDEX idx\_parcel\_risk ON parcel (risk\_score DESC);  
CREATE INDEX idx\_stage\_parcel ON acquisition\_stage (parcel\_id);  
CREATE INDEX idx\_stage\_status ON acquisition\_stage (status);  
CREATE INDEX idx\_audit\_entity ON audit\_log (entity\_type, entity\_id);  
CREATE INDEX idx\_audit\_user ON audit\_log (user\_id);  
CREATE INDEX idx\_audit\_timestamp ON audit\_log (created\_at DESC);  
CREATE INDEX idx\_history\_project ON project\_history (project\_id, snapshot\_date);  
CREATE INDEX idx\_document\_entity ON document (entity\_type, entity\_id);  
CREATE INDEX idx\_alert\_user\_read ON alert (user\_id, is\_read);

### **3.3 Enumerations**

\# Stage Names (default national workflow)  
STAGES \= \[  
    "PROPOSAL",  
    "IDENTIFICATION",  
    "SURVEY",  
    "VERIFICATION",  
    "NOTIFICATION",  
    "OBJECTION",  
    "AWARD",  
    "COMPENSATION",  
    "REHABILITATION\_RESETTLEMENT",  
    "POSSESSION",  
    "CLOSURE"  
\]

\# Parcel Status  
PARCEL\_STATUS \= \["NOT\_STARTED", "IN\_PROGRESS", "BLOCKED", "COMPLETED", "DISPUTED"\]

\# Project Status  
PROJECT\_STATUS \= \["PLANNING", "ACTIVE", "ON\_HOLD", "COMPLETED", "CANCELLED"\]

\# User Roles  
ROLES \= \["CENTRAL", "STATE", "DISTRICT", "PROJECT\_AGENCY", "FIELD\_OFFICER", "ADMIN"\]

\# Alert Severity  
ALERT\_SEVERITY \= \["INFO", "WARNING", "CRITICAL"\]

\# Document Types  
DOC\_TYPES \= \[  
    "NOTIFICATION", "SURVEY\_REPORT", "OWNERSHIP\_RECORD", "AWARD\_ORDER",  
    "COMPENSATION\_RECEIPT", "RR\_PLAN", "POSSESSION\_ORDER", "MAP", "OTHER"  
\]

────────────────────────────────────────────────────────────

## **4\. API Specification**

### **4.1 Base Configuration**

Base URL: /api/v1  
Content-Type: application/json  
Auth: Bearer \<JWT token\>  
Rate Limit: 100 requests/min per user

### **4.2 Authentication Endpoints**

| Method | Endpoint | Description | Auth |
| :---- | :---- | :---- | :---- |
| POST | /auth/login | Login, returns JWT | Public |
| POST | /auth/register | Register (admin-only creation) | Admin |
| POST | /auth/refresh | Refresh JWT token | Bearer |
| POST | /auth/logout | Invalidate session | Bearer |
| GET | /auth/me | Get current user profile | Bearer |

### **4.3 Project Endpoints**

| Method | Endpoint | Description | Roles |
| :---- | :---- | :---- | :---- |
| GET | /projects | List projects (scoped by role/geography) | All |
| GET | /projects/{id} | Get project detail | All |
| POST | /projects | Create project | Central, State, Admin |
| PUT | /projects/{id} | Update project | Central, State, Admin |
| DELETE | /projects/{id} | Archive project | Admin |
| GET | /projects/{id}/summary | Project metrics summary | All |
| GET | /projects/{id}/timeline | Project timeline events | All |

### **4.4 Parcel Endpoints**

| Method | Endpoint | Description | Roles |
| :---- | :---- | :---- | :---- |
| GET | /projects/{pid}/parcels | List parcels for project | All |
| GET | /parcels/{id} | Get parcel detail | All |
| POST | /projects/{pid}/parcels | Create parcel | State, District, Field |
| PUT | /parcels/{id} | Update parcel | State, District, Field |
| POST | /parcels/{id}/transition | Transition to next stage | District, Field |
| GET | /parcels/{id}/history | Get parcel stage history | All |
| GET | /parcels/{id}/risk | Get parcel risk detail | All |

### **4.5 GIS Endpoints**

| Method | Endpoint | Description | Roles |
| :---- | :---- | :---- | :---- |
| GET | /gis/projects/{id}/geojson | Project parcels as GeoJSON | All |
| GET | /gis/projects/{id}/corridor | Project corridor geometry | All |
| GET | /gis/boundaries/{level} | Admin boundaries (state/district/village) | All |
| POST | /gis/parcels/within | Parcels within a bounding box | All |
| GET | /gis/parcels/{id}/geometry | Single parcel geometry | All |

### **4.6 Dashboard / Analytics Endpoints**

| Method | Endpoint | Description | Roles |
| :---- | :---- | :---- | :---- |
| GET | /dashboard/national | National summary | Central, Admin |
| GET | /dashboard/state/{state} | State summary | Central, State |
| GET | /dashboard/district/{district} | District summary | All scoped |
| GET | /dashboard/project/{id} | Project dashboard data | All |
| GET | /analytics/bottleneck/{project\_id} | Bottleneck analysis | All |
| GET | /analytics/delay-risk/{project\_id} | Delay-risk predictions | All |
| GET | /analytics/priority/{project\_id} | Priority ranked cases | All |
| GET | /analytics/why-delayed/{parcel\_id} | Explainable delay factors | All |
| GET | /analytics/intervention/{project\_id} | Intervention recommendations | State, District |

### **4.7 Document Endpoints**

| Method | Endpoint | Description | Roles |
| :---- | :---- | :---- | :---- |
| POST | /documents/upload | Upload document | All (scoped) |
| GET | /documents/{id} | Download document | All (scoped) |
| GET | /documents/entity/{type}/{id} | List documents for entity | All (scoped) |
| GET | /documents/{id}/versions | Document version history | All (scoped) |

### **4.8 Alert / Notification Endpoints**

| Method | Endpoint | Description | Roles |
| :---- | :---- | :---- | :---- |
| GET | /alerts | Get user alerts | All |
| PUT | /alerts/{id}/read | Mark alert as read | All |
| GET | /alerts/unread/count | Unread count | All |

### **4.9 Admin Endpoints**

| Method | Endpoint | Description | Roles |
| :---- | :---- | :---- | :---- |
| GET | /admin/users | List users | Admin |
| POST | /admin/users | Create user | Admin |
| PUT | /admin/users/{id} | Update user | Admin |
| GET | /admin/audit-log | Query audit log | Admin |
| GET | /admin/workflow-templates | List workflow templates | Admin |
| POST | /admin/workflow-templates | Create workflow template | Admin |

### **4.10 Report Endpoints**

| Method | Endpoint | Description | Roles |
| :---- | :---- | :---- | :---- |
| POST | /reports/generate | Generate MIS report | All |
| GET | /reports/{id}/download | Download generated report | All |

────────────────────────────────────────────────────────────

## **5\. Authentication & Authorization Implementation**

### **5.1 JWT Token Structure**

{  
  "sub": "user\_uuid",  
  "username": "district\_officer\_01",  
  "role": "DISTRICT",  
  "state\_scope": "Uttar Pradesh",  
  "district\_scope": "Gautam Buddha Nagar",  
  "exp": 1725000000,  
  "iat": 1724996400  
}

### **5.2 Access Control Matrix**

| Resource | Central | State | District | Project Agency | Field Officer | Admin |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| National dashboard | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| State dashboard | ✅ | ✅ (own) | ❌ | ❌ | ❌ | ✅ |
| District dashboard | ✅ | ✅ (own state) | ✅ (own) | ❌ | ❌ | ✅ |
| Create project | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Create parcel | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Transition stage | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ |
| Upload document | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View analytics | ✅ | ✅ (own scope) | ✅ (own scope) | ✅ (own project) | ❌ | ✅ |
| Manage users | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| View audit log | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

### **5.3 Geographic Scope Enforcement**

\# Middleware pseudocode  
def enforce\_scope(user, resource):  
    if user.role \== "CENTRAL" or user.role \== "ADMIN":  
        return True  \# national scope  
    if user.role \== "STATE":  
        return resource.state \== user.state\_scope  
    if user.role \== "DISTRICT":  
        return (resource.state \== user.state\_scope and   
                resource.district \== user.district\_scope)  
    if user.role \== "PROJECT\_AGENCY":  
        return resource.project\_id in user.assigned\_projects  
    if user.role \== "FIELD\_OFFICER":  
        return resource.assigned\_officer \== user.id

────────────────────────────────────────────────────────────

## **6\. GIS Engine Specification**

### **6.1 Coordinate System**

* **SRID 4326** (WGS 84\) for storage and API exchange  
* Leaflet/MapLibre renders in Web Mercator (EPSG:3857) automatically

### **6.2 Geometry Operations**

| Operation | Library | Use Case |
| :---- | :---- | :---- |
| Parcel storage | PostGIS (POLYGON) | Persistent spatial data |
| Corridor buffer | PostGIS ST\_Buffer | Project footprint |
| Intersection | PostGIS ST\_Intersects | Find affected parcels |
| Area calculation | PostGIS ST\_Area | Land area metrics |
| Validation | PostGIS ST\_IsValid | Input validation |
| GeoJSON export | PostGIS ST\_AsGeoJSON | API response |
| Bounding box query | PostGIS ST\_Within \+ ST\_MakeEnvelope | Viewport loading |

### **6.3 Map Tile Sources**

| Source | Purpose |
| :---- | :---- |
| OpenStreetMap | Base map tiles |
| Stamen / CartoDB | Alternative base styles |
| Custom GeoJSON | Admin boundaries, parcels, corridors |

### **6.4 Viewport-Based Loading**

Client sends bounding box → /gis/parcels/within  
Backend: SELECT \* FROM parcel WHERE ST\_Intersects(geometry, ST\_MakeEnvelope(...))  
Returns GeoJSON FeatureCollection (max 500 features per request)

────────────────────────────────────────────────────────────

## **7\. ML/AI Pipeline Specification**

### **7.1 Delay-Risk Model**

| Aspect | Detail |
| :---- | :---- |
| Algorithm | XGBoost classifier (binary: elevated risk / normal) |
| Training data | project\_history snapshots (synthetic) |
| Features | days\_in\_current\_stage, backlog\_count, backlog\_trend (slope), processing\_rate, stage\_complexity\_score, compensation\_pending\_ratio, rr\_pending\_ratio, historical\_breach\_count, district\_capacity\_score |
| Target | is\_delayed\_30d (1 if project/parcel breaches SLA in next 30 days) |
| Output | Probability \[0.0–1.0\] \+ confidence band |
| Evaluation | Precision, Recall, F1, ROC-AUC on held-out test set |
| Fallback | If \< 5 snapshots exist → return "insufficient data" |

### **7.2 Bottleneck Detection**

\# Logic: Stage with highest (pending\_count × avg\_days\_pending)  
bottleneck\_score \= pending\_count\_per\_stage \* avg\_days\_in\_stage  
primary\_bottleneck \= max(stages, key=bottleneck\_score)

### **7.3 Priority Ranking**

\# Logic: Cases ranked by (impact × urgency)  
priority\_score \= (  
    downstream\_parcels\_blocked \* 0.4 \+  
    days\_overdue / sla\_days \* 0.3 \+  
    risk\_score \* 0.2 \+  
    compensation\_amount\_pending \* 0.1  
)

### **7.4 "Why Delayed?" Explainability**

* XGBoost feature importance (SHAP values for top-N features)  
* Human-readable factor labels:  
* "Ownership verification has been pending for 45 days (SLA: 30 days)"  
* "Processing rate dropped 30% in last 2 snapshots"  
* "3 parcels in this cluster have legal disputes"

### **7.5 Model Artifact Management**

/ml/  
├── models/  
│   ├── delay\_risk\_v1.joblib  
│   └── metadata.json          \# training date, metrics, feature list  
├── training/  
│   ├── train\_delay\_model.py  
│   └── evaluate\_model.py  
└── inference/  
    └── predict.py

────────────────────────────────────────────────────────────

## **8\. Document Management**

### **8.1 Upload Flow**

Client → multipart/form-data → FastAPI  
  → Validate file type (PDF, PNG, JPG, DOCX)  
  → Validate file size (max 10MB)  
  → Compute SHA-256 hash  
  → Store to /documents/{entity\_type}/{entity\_id}/{filename}  
  → Save metadata to documents table  
  → Increment version if same document type exists  
  → Create audit log entry

### **8.2 Allowed File Types**

ALLOWED\_TYPES \= {  
    "application/pdf",  
    "image/png", "image/jpeg",  
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"  
}  
MAX\_FILE\_SIZE \= 10 \* 1024 \* 1024  \# 10MB

────────────────────────────────────────────────────────────

## **9\. Deployment Architecture**

### **9.1 Docker Compose Services**

services:  
  frontend:  
    build: ./frontend  
    ports: \["3000:3000"\]  
    depends\_on: \[backend\]  
      
  backend:  
    build: ./backend  
    ports: \["8000:8000"\]  
    depends\_on: \[db\]  
    environment:  
      \- DATABASE\_URL=postgresql://...  
      \- JWT\_SECRET=...  
      \- CORS\_ORIGINS=http://localhost:3000  
    volumes:  
      \- ./documents:/app/documents  
      \- ./ml/models:/app/ml/models  
      
  db:  
    image: postgis/postgis:16-3.4  
    ports: \["5432:5432"\]  
    environment:  
      \- POSTGRES\_DB=bhoomisetu  
      \- POSTGRES\_USER=bhoomisetu  
      \- POSTGRES\_PASSWORD=...  
    volumes:  
      \- pgdata:/var/lib/postgresql/data  
      \- ./backend/db/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:  
  pgdata:

### **9.2 Environment Variables**

\# Backend  
DATABASE\_URL=postgresql+asyncpg://bhoomisetu:password@db:5432/bhoomisetu  
JWT\_SECRET=\<random-256-bit-key\>  
JWT\_ALGORITHM=HS256  
JWT\_EXPIRY\_MINUTES=60  
CORS\_ORIGINS=http://localhost:3000  
DOCUMENT\_STORAGE\_PATH=/app/documents  
ML\_MODEL\_PATH=/app/ml/models  
LOG\_LEVEL=INFO

\# Frontend  
VITE\_API\_BASE\_URL=http://localhost:8000/api/v1  
VITE\_MAP\_TILE\_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png

────────────────────────────────────────────────────────────

## **10\. Directory Structure**

bhoomisetu/  
├── docker-compose.yml  
├── README.md  
├── .env.example  
│  
├── frontend/  
│   ├── Dockerfile  
│   ├── package.json  
│   ├── tsconfig.json  
│   ├── vite.config.ts  
│   ├── tailwind.config.js  
│   ├── public/  
│   ├── src/  
│   │   ├── main.tsx  
│   │   ├── App.tsx  
│   │   ├── api/                  \# API client functions  
│   │   │   ├── client.ts  
│   │   │   ├── auth.ts  
│   │   │   ├── projects.ts  
│   │   │   ├── parcels.ts  
│   │   │   ├── gis.ts  
│   │   │   ├── analytics.ts  
│   │   │   └── documents.ts  
│   │   ├── components/  
│   │   │   ├── ui/               \# shadcn components  
│   │   │   ├── layout/           \# Header, Sidebar, Footer  
│   │   │   ├── dashboard/        \# Dashboard widgets  
│   │   │   ├── map/              \# GIS map components  
│   │   │   ├── project/          \# Project CRUD  
│   │   │   ├── parcel/           \# Parcel CRUD \+ workflow  
│   │   │   ├── analytics/        \# Charts, risk, bottleneck  
│   │   │   └── documents/        \# Document upload/list  
│   │   ├── hooks/                \# Custom React hooks  
│   │   ├── pages/                \# Route pages  
│   │   ├── store/                \# Zustand stores  
│   │   ├── types/                \# TypeScript interfaces  
│   │   └── utils/                \# Helpers, formatters  
│   └── tests/  
│  
├── backend/  
│   ├── Dockerfile  
│   ├── requirements.txt  
│   ├── pyproject.toml  
│   ├── app/  
│   │   ├── main.py               \# FastAPI app, middleware  
│   │   ├── config.py             \# Settings  
│   │   ├── database.py           \# DB engine, session  
│   │   ├── models/               \# SQLAlchemy models  
│   │   │   ├── user.py  
│   │   │   ├── project.py  
│   │   │   ├── parcel.py  
│   │   │   ├── stage.py  
│   │   │   ├── compensation.py  
│   │   │   ├── rr\_record.py  
│   │   │   ├── document.py  
│   │   │   ├── audit\_log.py  
│   │   │   └── project\_history.py  
│   │   ├── schemas/              \# Pydantic schemas  
│   │   ├── routers/              \# API route handlers  
│   │   │   ├── auth.py  
│   │   │   ├── projects.py  
│   │   │   ├── parcels.py  
│   │   │   ├── gis.py  
│   │   │   ├── dashboard.py  
│   │   │   ├── analytics.py  
│   │   │   ├── documents.py  
│   │   │   ├── alerts.py  
│   │   │   └── admin.py  
│   │   ├── services/             \# Business logic  
│   │   ├── middleware/           \# Auth, CORS, logging  
│   │   ├── utils/                \# Helpers  
│   │   └── ml/                   \# ML pipeline  
│   │       ├── models/  
│   │       ├── training/  
│   │       └── inference/  
│   ├── db/  
│   │   ├── init.sql              \# Schema \+ PostGIS  
│   │   ├── seed.py               \# Synthetic data generator  
│   │   └── migrations/           \# Alembic migrations  
│   └── tests/  
│  
├── data/  
│   ├── boundaries/               \# GeoJSON boundary files  
│   ├── synthetic/                \# Generated demo data  
│   └── ml\_training/              \# Training datasets  
│  
└── docs/  
    ├── PRD.md  
    ├── TRD.md  
    └── API.md

────────────────────────────────────────────────────────────

## **11\. Performance Targets**

| Metric | Target | Measurement |
| :---- | :---- | :---- |
| API response (simple CRUD) | \< 200ms | p95 latency |
| API response (analytics) | \< 500ms | p95 latency |
| Dashboard full load | \< 3 seconds | Time to interactive |
| GIS map initial render | \< 2 seconds | First meaningful paint |
| GIS parcel query (viewport) | \< 500ms | PostGIS spatial query |
| File upload (10MB) | \< 5 seconds | End-to-end |
| ML prediction (single project) | \< 1 second | Inference time |
| Concurrent users (demo) | 20+ | No degradation |
| Database queries | \< 100ms | p95 for indexed queries |

────────────────────────────────────────────────────────────

## **12\. Error Handling Standards**

### **12.1 API Error Response Format**

{  
  "detail": {  
    "code": "PARCEL\_NOT\_FOUND",  
    "message": "Parcel with ID xyz not found",  
    "timestamp": "2026-09-01T12:00:00Z"  
  }  
}

### **12.2 HTTP Status Codes**

| Code | Usage |
| :---- | :---- |
| 200 | Successful GET/PUT |
| 201 | Successful POST (created) |
| 204 | Successful DELETE |
| 400 | Validation error |
| 401 | Missing/invalid token |
| 403 | Insufficient permissions |
| 404 | Resource not found |
| 409 | Conflict (duplicate) |
| 413 | File too large |
| 422 | Invalid request body |
| 429 | Rate limit exceeded |
| 500 | Internal server error |

────────────────────────────────────────────────────────────

## **13\. Coding Standards**

### **13.1 Backend (Python)**

* PEP 8 compliance  
* Type hints on all function signatures  
* Docstrings on all public functions  
* Async handlers where I/O is involved  
* Pydantic models for all request/response schemas  
* SQL queries through SQLAlchemy ORM (no raw SQL except PostGIS)

### **13.2 Frontend (TypeScript)**

* Strict TypeScript mode (strict: true)  
* Functional components with hooks only  
* Named exports for components  
* Interface-first approach for API types  
* Error boundaries at page level  
* Loading states for all async operations

### **13.3 Git Conventions**

* Branch naming: feature/, fix/, hotfix/  
* Commit messages: feat:, fix:, docs:, chore:, test:  
* PR required for main branch  
* No force-push to main
# **BhoomiSetu — Feature Ticket List**

**Project:** BhoomiSetu | SIH26016 | SIH 2026

**Version:** 1.0

**Date:** 2026-09-01

**Total Tickets:** 48

**Estimated Total Story Points:** \~180

────────────────────────────────────────────────────────────

## **Priority Legend**

| Priority | Meaning | When |
| :---- | :---- | :---- |
| P0 | Must have for demo | Day 1–2 |
| P1 | Should have for intelligence layer | Day 2–3 |
| P2 | Nice to have / polish | Day 3–5 |

## **Team Legend**

| Code | Team |
| :---- | :---- |
| BE | Backend (2 developers) |
| FE | Frontend (2 developers) |
| RS | Research & Presentation (2 members) |

────────────────────────────────────────────────────────────

## **Epic 1: Authentication & RBAC**

### **TICK-001: Backend — JWT Authentication System**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | None |
| Description | Implement JWT-based auth with login, logout, token refresh. bcrypt password hashing, 60-min access token, 7-day refresh token. |
| Acceptance Criteria | ✅ POST /auth/login returns JWT \+ refresh token ✅ POST /auth/refresh rotates tokens ✅ POST /auth/logout invalidates refresh token ✅ Invalid/expired token returns 401 ✅ Failed login lockout after 5 attempts |

### **TICK-002: Backend — RBAC Middleware & Scope Filter**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-001 |
| Description | Implement role-based access control middleware. Geographic scope enforcement at query level (Central=national, State=own state, District=own district, Project Agency=assigned projects, Field Officer=assigned parcels). |
| Acceptance Criteria | ✅ Each role sees only scoped data ✅ District officer cannot access another district ✅ Unauthorized access returns 403 ✅ Role check on every protected endpoint |

### **TICK-003: Frontend — Login Page**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 3 |
| Dependencies | TICK-001 |
| Description | Build login page with username/password form, error handling, loading states. Store JWT in memory/store, redirect to dashboard. |
| Acceptance Criteria | ✅ Form validates required fields ✅ Shows error on invalid credentials ✅ Shows loading spinner during auth ✅ Redirects to /dashboard on success ✅ Auto-redirects if already authenticated |

### **TICK-004: Frontend — Auth Guard & Protected Routes**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 3 |
| Dependencies | TICK-003 |
| Description | Implement route protection. Redirect unauthenticated users to /login. Role-based route filtering (hide admin nav for non-admins). Auto-refresh token on 401\. |
| Acceptance Criteria | ✅ Unauthenticated users redirected to /login ✅ Role-based navigation items ✅ Auto token refresh on 401 ✅ Logout clears all state and redirects |

────────────────────────────────────────────────────────────

## **Epic 2: Project Management**

### **TICK-005: Backend — Project CRUD APIs**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-002 |
| Description | Implement GET/POST/PUT/DELETE for projects. Include filters (state, status, type), pagination, search. Scope enforcement. |
| Acceptance Criteria | ✅ CRUD operations work ✅ Pagination with limit/offset ✅ Filter by state, status, type ✅ Search by name ✅ Scoped by user role/geography |

### **TICK-006: Backend — Project Summary & Metrics API**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-005, TICK-009 |
| Description | Compute project-level metrics: total parcels, acquired count, pending by stage, compensation metrics, R\&R metrics, SLA breach count. |
| Acceptance Criteria | ✅ GET /projects/{id}/summary returns all metrics ✅ Stage-wise parcel distribution ✅ Compensation totals ✅ R\&R counts ✅ SLA breach count |

### **TICK-007: Frontend — Project List Page**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 5 |
| Dependencies | TICK-005 |
| Description | Sortable, filterable table of projects. Progress bar, risk badge, status badge. Filters for state/status/type. Search bar. Pagination. |
| Acceptance Criteria | ✅ Table renders with all columns ✅ Sort by any column ✅ Filter by state, status, type ✅ Search works ✅ Click row navigates to detail ✅ Loading/empty states |

### **TICK-008: Frontend — Project Detail Page (Overview Tab)**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 8 |
| Dependencies | TICK-006 |
| Description | Project detail with tabs: Overview, Parcels, Map, Intelligence, Documents. Overview tab: 5 stat cards, stage breakdown chart, acquisition timeline chart. |
| Acceptance Criteria | ✅ Tab navigation works ✅ Stat cards show correct metrics ✅ Stage breakdown horizontal bar chart ✅ Timeline line chart from snapshots ✅ Responsive layout |

────────────────────────────────────────────────────────────

## **Epic 3: Parcel Management & Workflow**

### **TICK-009: Backend — Parcel CRUD APIs**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-005 |
| Description | Implement GET/POST/PUT for parcels within projects. Fields: survey\_number, area, geometry, owner, stage, status. Filters by stage, status, risk. Scope enforcement. |
| Acceptance Criteria | ✅ Create parcel with geometry (GeoJSON) ✅ List parcels with filters and pagination ✅ Get single parcel with full details ✅ Update parcel fields ✅ Scoped by user role/geography |

### **TICK-010: Backend — Parcel Stage Transition API**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 8 |
| Dependencies | TICK-009 |
| Description | Implement POST /parcels/{id}/transition. Validate stage ordering (can't skip stages). Update current\_stage, create acquisition\_stage record, update timestamps. Check SLA. Create audit log entry. Trigger alert on SLA breach. |
| Acceptance Criteria | ✅ Stage transition follows correct order ✅ Cannot skip stages ✅ Creates acquisition\_stage record ✅ Updates parcel.current\_stage ✅ Audit log created ✅ SLA breach detected and alerted |

### **TICK-011: Frontend — Parcel List (Project Detail Parcels Tab)**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 5 |
| Dependencies | TICK-009 |
| Description | Filterable, sortable table of parcels within a project. Columns: survey\#, area, stage, status, risk, officer, days pending. Status/risk badges. Click → parcel detail. |
| Acceptance Criteria | ✅ All columns render ✅ Filter by stage, status ✅ Sort by any column ✅ Risk/status badges ✅ Click navigates to parcel detail |

### **TICK-012: Frontend — Parcel Detail Page**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 8 |
| Dependencies | TICK-010 |
| Description | Full parcel detail: header with key info, workflow pipeline visualization (stages as horizontal steps with icons), compensation section, R\&R section, document list, audit timeline. "Advance to Next Stage" button (role-gated). |
| Acceptance Criteria | ✅ Workflow pipeline shows completed/current/pending stages ✅ SLA breach indicator on overdue stages ✅ Stage transition button works (role-gated) ✅ Compensation and R\&R sections display ✅ Audit timeline renders chronologically |

────────────────────────────────────────────────────────────

## **Epic 4: GIS Map**

### **TICK-013: Backend — GIS APIs**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-009 |
| Description | Implement GIS endpoints: project parcels as GeoJSON FeatureCollection, project corridor geometry, admin boundaries, parcels within bounding box. Viewport-based loading (max 500 features). |
| Acceptance Criteria | ✅ Returns valid GeoJSON ✅ Viewport-based query works ✅ Max 500 features per request ✅ Color-coding data included in properties ✅ Scoped by user role/geography |

### **TICK-014: Frontend — GIS Map Page**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 8 |
| Dependencies | TICK-013 |
| Description | Full-screen Leaflet/MapLibre map. Project selector. Color-coded parcel polygons (green/yellow/red/grey). Click parcel → popup with summary \+ link to detail. Layer controls. Legend. Status filters. Viewport-based loading. |
| Acceptance Criteria | ✅ Map renders with OSM tiles ✅ Parcel polygons color-coded by status ✅ Click parcel shows popup ✅ Layer toggle works ✅ Status filter shows/hides parcels ✅ Loads parcels based on viewport |

### **TICK-015: Frontend — Embedded Map in Project Detail**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | FE |
| Points | 3 |
| Dependencies | TICK-014 |
| Description | Embed the GIS map component in the Project Detail "Map" tab, auto-scoped to the selected project's corridor and parcels. |
| Acceptance Criteria | ✅ Map auto-centers on project corridor ✅ Shows only project's parcels ✅ Same interactions as full map page |

────────────────────────────────────────────────────────────

## **Epic 5: Dashboard**

### **TICK-016: Backend — National Dashboard API**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-006 |
| Description | Aggregate national-level metrics: active projects, total land, acquisition percentage, SLA breaches, stage distribution, state-wise summary. |
| Acceptance Criteria | ✅ Returns all KPI metrics ✅ State-wise breakdown ✅ Stage distribution ✅ Compensation totals ✅ Runs in \< 500ms |

### **TICK-017: Backend — State/District Dashboard APIs**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | BE |
| Points | 3 |
| Dependencies | TICK-016 |
| Description | Same as national but scoped to state or district. District-wise breakdown for state view, project-level for district view. |
| Acceptance Criteria | ✅ State dashboard shows district breakdown ✅ District dashboard shows project breakdown ✅ Scoped by user role |

### **TICK-018: Frontend — National Dashboard**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 8 |
| Dependencies | TICK-016 |
| Description | 4 stat cards (projects, land, acquired%, breaches), stage distribution donut, acquisition progress stacked bar by state, compensation bar chart, high-risk projects table, state-wise summary table. Auto-refresh every 60s. |
| Acceptance Criteria | ✅ All 4 stat cards render ✅ Charts display correctly ✅ High-risk table shows top 10 ✅ State table is sortable ✅ Auto-refresh works ✅ Loading skeletons show |

### **TICK-019: Frontend — State/District Dashboard**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | FE |
| Points | 5 |
| Dependencies | TICK-017, TICK-018 |
| Description | Reuse dashboard components but scoped. State → district breakdown. District → project breakdown. Appropriate breadcrumbs and navigation. |
| Acceptance Criteria | ✅ Scope-appropriate data ✅ Drill-down navigation ✅ Breadcrumbs work |

────────────────────────────────────────────────────────────

## **Epic 6: Analytics & Intelligence**

### **TICK-020: Backend — Bottleneck Detection API**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-009 |
| Description | Compute bottleneck: stage with highest (pending\_count × avg\_days\_pending). Return primary bottleneck, all stage scores, breach rates. |
| Acceptance Criteria | ✅ Identifies correct bottleneck stage ✅ Returns all stage metrics ✅ Handles edge cases (empty project) |

### **TICK-021: Backend — Delay-Risk Prediction API**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | BE |
| Points | 8 |
| Dependencies | TICK-031 |
| Description | Load trained XGBoost model. Compute features from project\_history. Return risk score \[0-1\] with confidence. SHAP feature importance for explainability. Graceful degradation if \< 5 snapshots. |
| Acceptance Criteria | ✅ Returns probability score ✅ Returns feature importance ✅ Returns "insufficient data" when appropriate ✅ Runs in \< 1 second ✅ Confidence scoring works |

### **TICK-022: Backend — Priority Ranking & Intervention API**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-020, TICK-021 |
| Description | Rank parcels by priority\_score \= (downstream\_impact × 0.4 \+ overdue\_ratio × 0.3 \+ risk × 0.2 \+ compensation\_pending × 0.1). Generate intervention text recommendations. |
| Acceptance Criteria | ✅ Returns ranked list ✅ Scores are reasonable ✅ Recommendations are generated ✅ Handles edge cases |

### **TICK-023: Backend — "Why Delayed?" API**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | BE |
| Points | 3 |
| Dependencies | TICK-020, TICK-021 |
| Description | For a given parcel, return human-readable explanation of delay factors: current stage duration vs SLA, processing rate trend, adjacent disputes, compensation status. |
| Acceptance Criteria | ✅ Returns structured factor breakdown ✅ Includes SLA comparison ✅ Human-readable text |

### **TICK-024: Frontend — Analytics Page**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | FE |
| Points | 8 |
| Dependencies | TICK-020, TICK-021, TICK-022, TICK-023 |
| Description | Full analytics page: project selector, delay-risk gauge/score, bottleneck summary card, SHAP feature importance horizontal bar chart, prioritized interventions table, intervention recommendation card. |
| Acceptance Criteria | ✅ Risk score displays with color coding ✅ Feature importance chart renders ✅ Intervention table is sortable ✅ Recommendation card shows ✅ "Insufficient data" state handled |

### **TICK-025: Frontend — Intelligence Tab in Project Detail**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | FE |
| Points | 3 |
| Dependencies | TICK-024 |
| Description | Embed analytics components in the Project Detail "Intelligence" tab, auto-scoped to the project. |
| Acceptance Criteria | ✅ Shows same data as analytics page but project-scoped |

────────────────────────────────────────────────────────────

## **Epic 7: Documents**

### **TICK-026: Backend — Document Upload/Download APIs**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-002 |
| Description | File upload (multipart), validation (type, size, magic bytes), SHA-256 hash, UUID rename, version tracking. Download via authenticated endpoint. List by entity. |
| Acceptance Criteria | ✅ Upload works for PDF, PNG, JPG, DOCX ✅ Rejects disallowed types ✅ Rejects \>10MB ✅ Stores with UUID filename ✅ Version increments on re-upload ✅ Download requires auth |

### **TICK-027: Frontend — Document Upload & List**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | FE |
| Points | 5 |
| Dependencies | TICK-026 |
| Description | Drag-and-drop upload component. Document list with type, date, uploader, version. Preview for PDF/images. Download button. Document tab in parcel/project detail. |
| Acceptance Criteria | ✅ Drag-and-drop works ✅ Progress indicator during upload ✅ Document list renders ✅ Preview works for PDF/images ✅ Download button works |

────────────────────────────────────────────────────────────

## **Epic 8: Alerts & Notifications**

### **TICK-028: Backend — Alerts System**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | BE |
| Points | 3 |
| Dependencies | TICK-010 |
| Description | Create alerts on: SLA breach, stage completion, parcel status change. Store in alerts table. API: list (paginated), mark read, unread count. |
| Acceptance Criteria | ✅ Alerts created on trigger events ✅ Routed to correct user by role/scope ✅ List/read/count APIs work |

### **TICK-029: Frontend — Alerts Page & Header Badge**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | FE |
| Points | 3 |
| Dependencies | TICK-028 |
| Description | Alerts page: list with severity icons, messages, timestamps, entity links. Mark read. Header bell icon with unread count badge. |
| Acceptance Criteria | ✅ Alert list renders ✅ Severity icons correct ✅ Mark read works ✅ Badge shows unread count ✅ Click alert navigates to entity |

────────────────────────────────────────────────────────────

## **Epic 9: Admin**

### **TICK-030: Frontend — Admin Page (Users \+ Audit Log)**

| Field | Value |
| :---- | :---- |
| Priority | P2 |
| Team | FE |
| Points | 5 |
| Dependencies | TICK-002 |
| Description | Admin page with tabs: Users (list, create, edit role/scope), Audit Log (searchable, filterable by user/action/date). Admin-only access. |
| Acceptance Criteria | ✅ User CRUD works ✅ Role/scope assignment ✅ Audit log searchable ✅ Date range filter ✅ Only ADMIN role can access |

────────────────────────────────────────────────────────────

## **Epic 10: Data & ML**

### **TICK-031: Data — Synthetic Data Generator (Seed Script)**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | RS \+ BE |
| Points | 8 |
| Dependencies | DB schema (TICK-005, TICK-009) |
| Description | Python seed script: create 10-20 projects, 2000-5000 parcels with realistic distributions, compensation/R\&R records, historical snapshots, demo user accounts. Use real admin boundaries (SoI/OSM). Parcel geometries inside real village polygons. Inject varied bottleneck profiles. |
| Acceptance Criteria | ✅ 10+ projects with varied states ✅ 2000+ parcels with valid geometry ✅ Historical snapshots (15-day intervals) ✅ Realistic stage distributions ✅ 3-5 distinct bottleneck profiles ✅ Demo user accounts created ✅ All data labelled as synthetic |

### **TICK-032: Data — Real Administrative Boundaries (GeoJSON)**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | RS |
| Points | 5 |
| Dependencies | None |
| Description | Source real state/district/village boundaries from Survey of India or OSM. Convert to GeoJSON. Load into PostGIS. Select 3-5 demo districts with sufficient detail. |
| Acceptance Criteria | ✅ State boundaries loaded ✅ 3-5 district boundaries loaded ✅ 15-30 village boundaries loaded ✅ Valid GeoJSON ✅ Sources cited |

### **TICK-033: ML — Train Delay-Risk Model**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | RS |
| Points | 8 |
| Dependencies | TICK-031 |
| Description | Train XGBoost classifier on synthetic project\_history. Features: days\_in\_stage, backlog\_trend, processing\_rate, etc. Target: is\_delayed\_30d. Evaluate on held-out set. Export model as .joblib. Document metrics. |
| Acceptance Criteria | ✅ Model trained and saved ✅ F1 \> 0.7 on test set ✅ Feature importance extracted ✅ Confidence calibration checked ✅ Handles edge cases (insufficient data) |

### **TICK-034: Data — GIS Corridor & Parcel Geometry Generation**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | RS |
| Points | 5 |
| Dependencies | TICK-032 |
| Description | Create realistic project corridors from OSM road/rail data. Buffer corridors. Generate synthetic parcel polygons inside real village boundaries (Voronoi/subdivision). |
| Acceptance Criteria | ✅ Corridors follow real infrastructure ✅ Parcels are within village bounds ✅ Geometries are valid (ST\_IsValid) ✅ Visual inspection passes |

────────────────────────────────────────────────────────────

## **Epic 11: Testing**

### **TICK-035: Backend — API Unit & Integration Tests**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | All backend APIs |
| Description | pytest tests: auth flow, CRUD operations, scope enforcement, stage transitions, input validation, error handling. |
| Acceptance Criteria | ✅ Auth tests pass ✅ CRUD tests pass ✅ Scope tests: district can't access another district ✅ Invalid input rejected ✅ 80%+ coverage on routers |

### **TICK-036: Testing — Security Testing (Red Team)**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE \+ FE |
| Points | 5 |
| Dependencies | All features |
| Description | Test: SQL injection, XSS, privilege escalation, unauthorized scope access, file upload exploits, invalid GeoJSON, oversized payloads, rate limiting. |
| Acceptance Criteria | ✅ All injection attempts rejected ✅ Privilege escalation blocked ✅ Scope violations return 403 ✅ File exploits blocked ✅ Rate limits enforced |

### **TICK-037: Testing — End-to-End Workflow Testing**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | ALL |
| Points | 5 |
| Dependencies | All features |
| Description | Test complete workflows: login → create project → add parcels → transition stages → view dashboard → view map → check analytics → upload document → generate report. |
| Acceptance Criteria | ✅ Full demo flow works end-to-end ✅ All role perspectives tested ✅ No crashes or data corruption ✅ Dashboard metrics update correctly |

### **TICK-038: Testing — GIS Validation**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | BE \+ RS |
| Points | 3 |
| Dependencies | TICK-013, TICK-014 |
| Description | Test: malformed GeoJSON, self-intersecting polygons, out-of-bounds coordinates, oversized geometry, viewport loading performance. |
| Acceptance Criteria | ✅ Invalid geometry rejected ✅ Out-of-bounds rejected ✅ Oversized geometry rejected ✅ 500 parcels render in \< 2s |

### **TICK-039: Testing — AI/ML Edge Cases**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | RS |
| Points | 3 |
| Dependencies | TICK-033, TICK-021 |
| Description | Test: missing data → "insufficient data" response, extreme outliers, model instability, prediction with no history, incorrect confidence. |
| Acceptance Criteria | ✅ No fabricated confidence on empty data ✅ Outliers don't crash model ✅ Degradation is graceful ✅ Confidence band is reasonable |

────────────────────────────────────────────────────────────

## **Epic 12: Demo & Polish**

### **TICK-040: Frontend — App Layout Shell (Topbar, Sidebar, Routing)**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | FE |
| Points | 5 |
| Dependencies | TICK-004 |
| Description | Build the application shell: topbar with logo/search/notifications/user, collapsible sidebar with role-based nav items, main content area, breadcrumbs. Dark theme. |
| Acceptance Criteria | ✅ Sidebar toggles ✅ Role-based nav items ✅ Active route highlighted ✅ Responsive ✅ Dark theme |

### **TICK-041: Backend — Database Schema & Migrations**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 5 |
| Dependencies | None (Day 1 first task) |
| Description | Create PostgreSQL \+ PostGIS schema: all tables, indexes, enums, constraints. Alembic migration. Docker init script. |
| Acceptance Criteria | ✅ All tables created ✅ Spatial indexes ✅ Enums defined ✅ Foreign keys ✅ Docker init works ✅ Migration reversible |

### **TICK-042: DevOps — Docker Compose Setup**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | BE |
| Points | 3 |
| Dependencies | None (Day 1 first task) |
| Description | Docker Compose with frontend (Vite dev), backend (FastAPI/uvicorn), db (PostGIS). Volume mounts for hot reload. .env.example. README with setup instructions. |
| Acceptance Criteria | ✅ docker-compose up starts all services ✅ Hot reload works for FE and BE ✅ DB data persisted in volume ✅ README documents setup |

### **TICK-043: Frontend — MIS Report Generation Page**

| Field | Value |
| :---- | :---- |
| Priority | P2 |
| Team | FE |
| Points | 3 |
| Dependencies | Backend report API |
| Description | Report page: select type, date range, generate. Download PDF/Excel. Recent reports table. |
| Acceptance Criteria | ✅ Report generates ✅ Download works ✅ Loading state ✅ Recent reports listed |

### **TICK-044: Backend — Report Generation API**

| Field | Value |
| :---- | :---- |
| Priority | P2 |
| Team | BE |
| Points | 5 |
| Dependencies | TICK-016 |
| Description | Generate executive/project/state/district reports. Output as downloadable file. Include key metrics, charts data, and recommendations. |
| Acceptance Criteria | ✅ Report generates with correct data ✅ Scoped by user role ✅ Download works |

### **TICK-045: Backend — Audit Log API**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | BE |
| Points | 3 |
| Dependencies | TICK-002 |
| Description | Query audit log: filter by user, action, entity\_type, date range. Paginated. Admin-only. Append-only table constraint. |
| Acceptance Criteria | ✅ Query with filters works ✅ Paginated ✅ Admin-only access ✅ No UPDATE/DELETE allowed on table |

### **TICK-046: Demo — Demo Dataset Lock & Rehearsal**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | RS |
| Points | 3 |
| Dependencies | All features stable |
| Description | Lock the demo dataset. Verify all demo scenarios work. Rehearse the 10-step demo story. Prepare backup dataset. |
| Acceptance Criteria | ✅ Demo dataset reproducible ✅ All 10 demo steps work ✅ Backup dataset exists ✅ Demo timing \< 10 minutes |

### **TICK-047: Research — Pitch Deck & Presentation**

| Field | Value |
| :---- | :---- |
| Priority | P0 |
| Team | RS |
| Points | 8 |
| Dependencies | Working prototype |
| Description | Create SIH presentation: problem, solution, architecture, demo screenshots/video, tech stack, data strategy, team, impact. 60-second pitch script. Judge Q\&A preparation. |
| Acceptance Criteria | ✅ 15-20 slide deck ✅ Demo screenshots/video embedded ✅ 60-second pitch rehearsed ✅ Judge Q\&A answers prepared (20+ questions) |

### **TICK-048: Research — Data Sources Documentation & Citations**

| Field | Value |
| :---- | :---- |
| Priority | P1 |
| Team | RS |
| Points | 3 |
| Dependencies | TICK-032 |
| Description | Document all data sources with proper citations: DILRMP, LACRRIS, SoI, Bhuvan, OSM. Include reference panel in the app. Legal compliance notes. |
| Acceptance Criteria | ✅ All sources cited ✅ Licensing verified ✅ Reference panel content ready ✅ Synthetic data clearly labelled |

────────────────────────────────────────────────────────────

## **Ticket Summary**

| Epic | P0 | P1 | P2 | Total |
| :---- | :---- | :---- | :---- | :---- |
| Auth & RBAC | 4 | 0 | 0 | 4 |
| Projects | 3 | 0 | 0 | 3 (+1 shared) |
| Parcels & Workflow | 4 | 0 | 0 | 4 |
| GIS Map | 2 | 1 | 0 | 3 |
| Dashboard | 1 (+1 shared) | 2 | 0 | 3 (+1 shared) |
| Analytics & Intelligence | 0 | 6 | 0 | 6 |
| Documents | 1 | 1 | 0 | 2 |
| Alerts | 0 | 2 | 0 | 2 |
| Admin | 0 | 0 | 1 | 1 |
| Data & ML | 3 | 1 | 0 | 4 |
| Testing | 2 | 3 | 0 | 5 |
| Demo & Polish | 5 | 2 | 2 | 9 |
| TOTAL | 25 | 18 | 3 | 48 (incl. shared) |


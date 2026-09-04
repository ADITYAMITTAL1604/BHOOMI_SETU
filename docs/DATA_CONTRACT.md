# BhoomiSetu — Data Contract & Integration Specification

**SIH Problem Statement**: SIH26016  
**Document Version**: 1.0 (Production-Hardened)  
**Date**: September 2026  

---

## 1. Scope & Objective

This Data Contract establishes strict interface rules and typing specifications across:
1. Ingested data assets (`data/synthetic/` CSV & GeoJSON).
2. Backend Database Schema (`PostgreSQL` / `SQLite` via SQLAlchemy 2.0).
3. Machine Learning Inference Engine (10-feature vector contract).
4. REST API Payloads (FastAPI & Pydantic v2).
5. Frontend TypeScript Consumers (`bhoomisetu-frontend`).

---

## 2. Statutory Acquisition Stages & SLA Thresholds

Per the RFCTLARR Act (2013) and BhoomiSetu workflow specifications, acquisition consists of 11 sequential stages:

| Order | Code / Identifier | Display Label | Statutory SLA (Days) | Critical Failure Mode |
|:---:|:---|:---|:---:|:---|
| 1 | `SURVEY` | Survey / Parcel Mapping | 30 | Unverified parcel bounds |
| 2 | `VERIFICATION` | Ownership Verification | 45 | Title disputes / missing RoR |
| 3 | `PRELIMINARY_NOTIFICATION` | Section 11 Notification | 20 | Objections period lapse |
| 4 | `OBJECTION` | Objections & Hearings | 30 | High court litigation |
| 5 | `DECLARATION` | Section 19 Declaration | 30 | Statutory abandonment if >12mo |
| 6 | `AWARD` | Award Enquiry & Determination | 45 | Solatium & market value dispute |
| 7 | `COMPENSATION` | Compensation Disbursement | 30 | Unpaid escrow / bank failures |
| 8 | `REHABILITATION_RESETTLEMENT` | R&R Execution | 60 | Lack of developed house sites |
| 9 | `POSSESSION` | Physical Possession | 15 | Law and order resistance |
| 10 | `MUTATION` | Land Transfer / Mutation | 30 | Revenue record desynchronization |
| 11 | `CLOSURE` | Project Commissioning & Closure | 15 | Residual audit queries |

### SLA Breach Rule:
A parcel stage is classified as in breach (`sla_breach = 1` or `status = 'OVERDUE'`) if:
$$\text{elapsed\_days} > \text{target\_days} \quad \text{where stage status} \in \{\text{IN\_PROGRESS}, \text{BLOCKED}\}$$

---

## 3. Entity Schemas & Type Contracts

### 3.1 Project Entity
```typescript
interface Project {
  project_id: string;              // UUIDv4 (or deterministic UUIDv5)
  name: string;                    // Max 255 chars
  type: string;                    // "Highway" | "Railway" | "Port" | "Industrial" | "Transmission"
  states: string[];                // Non-empty array of valid Indian states
  districts: string[];             // Array of administrative district names
  land_required_ha: number;        // Float >= 0.01
  land_acquired_ha: number;        // Float >= 0.0, <= land_required_ha
  target_date: string;             // ISO-8601 Date (YYYY-MM-DD)
  status: "PLANNING" | "ACTIVE" | "COMPLETED" | "STALLED";
  corridor_geometry?: GeoJSON.LineString | string; // EPSG:4326
  created_at: string;              // ISO-8601 UTC
}
```

### 3.2 Parcel Entity
```typescript
interface Parcel {
  parcel_id: string;               // UUIDv4
  project_id: string;              // Foreign key to Project
  survey_number: string;           // E.g. "104/2A"
  area_ha: number;                 // Land area in hectares (>0.0)
  geometry: GeoJSON.Polygon;       // EPSG:4326 closed polygon
  owner_name: string;              // Registered khatedar / occupant
  owner_reference: string;         // Masked UID or RoR reference
  current_stage: StageName;        // Enum (1 of 11 stages)
  status: "NOT_STARTED" | "IN_PROGRESS" | "BLOCKED" | "DISPUTED" | "COMPLETED";
  risk_score: number;              // 0.0 to 100.0 (ML or heuristic)
  village: string;
  district: string;
  state: string;
  assigned_officer?: string;       // Foreign key to User
}
```

### 3.3 Compensation Entity (RFCTLARR 2013)
```typescript
interface Compensation {
  compensation_id: string;         // UUID
  parcel_id: string;               // UUID
  assessed_amount: number;         // Base market value (INR)
  approved_amount: number;         // Base + Multiplier (1.25-2.0) + 100% Solatium
  paid_amount: number;             // Amount successfully transferred
  payment_status: "PENDING" | "APPROVED" | "PARTIALLY_PAID" | "DISBURSED";
  payment_date?: string;           // ISO-8601 Date
  remarks?: string;
}
```

---

## 4. Machine Learning 10-Feature Vector Contract

The delay risk inference service (`delay_risk_model.joblib`) consumes a strictly ordered 10-dimensional numeric vector:

| Index | Feature Name | Dtype | Range | Imputation Strategy | Operational Definition |
|:---:|:---|:---:|:---:|:---|:---|
| 0 | `pending_parcels` | float | $\ge 0$ | Median | Count of parcels not yet at `CLOSURE`. |
| 1 | `completed_parcels` | float | $\ge 0$ | Median | Count of parcels at `CLOSURE`. |
| 2 | `average_stage_days` | float | $\ge 0$ | Median (35.0) | Mean days spent across active stages. |
| 3 | `sla_breaches` | float | $\ge 0$ | Zero | Count of stages currently exceeding target SLA. |
| 4 | `compensation_pending` | float | $\ge 0$ | Zero | Count of parcels where compensation status $\neq$ `DISBURSED`. |
| 5 | `rr_pending` | float | $\ge 0$ | Zero | Count of R&R cases where status $\neq$ `COMPLETED`. |
| 6 | `possession_pending` | float | $\ge 0$ | Zero | Count of parcels where possession has not been handed over. |
| 7 | `processing_rate` | float | $0.0 - 1.0$ | Median (0.15) | Ratio of completed to total parcels. |
| 8 | `pending_trend` | float | $[-10.0, 10.0]$ | Zero | Rate of change in pending parcel queue over last 30 days. |
| 9 | `rate_trend` | float | $[-1.0, 1.0]$ | Zero | Acceleration of parcel completion rate. |

**Inference Response Contract**:
```json
{
  "project_id": "uuid",
  "risk_score": 0.35,
  "risk_level": "medium",
  "top_factors": [
    { "factor": "sla_breaches", "impact": "+0.18", "description": "12 active SLA breaches in Award stage" }
  ],
  "feature_importance": [
    { "feature": "sla_breaches", "label": "SLA Breaches", "importance": 0.32, "direction": "positive" }
  ]
}
```

---

## 5. Security & Access Control Contract

| User Role | Read Scope | Mutate Scope | Protected Attributes |
|:---|:---|:---|:---|
| `ADMIN` | Global (All states & projects) | All entities | Full access |
| `CENTRAL` | Global (All states & projects) | Projects, Analytics | Cannot override raw parcel risk scores directly |
| `STATE` | Filtered by `user.state_scope` | Projects in state | Cannot view or edit other states |
| `DISTRICT` | Filtered by `user.district_scope` | Parcels in district | Restricted to assigned district |
| `PROJECT_AGENCY` | Filtered by assigned projects | Project proposals | Cannot approve compensation disbursements |
| `FIELD_OFFICER` | Assigned parcels in district | Survey & verification notes | Cannot modify `risk_score` or force stage bypass |

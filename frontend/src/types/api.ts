// ============================================
// BHOOMISETU SHARED TYPES — MUST MATCH BACKEND SCHEMAS
// ============================================

// ── Enums ──────────────────────────────────────────────

export type UserRole =
  | "CENTRAL"
  | "STATE"
  | "DISTRICT"
  | "PROJECT_AGENCY"
  | "FIELD_OFFICER"
  | "ADMIN";

export type ProjectStatus =
  | "PLANNING"
  | "ACTIVE"
  | "ON_HOLD"
  | "COMPLETED"
  | "CANCELLED";

export type ParcelStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "BLOCKED"
  | "COMPLETED"
  | "DISPUTED";

export type AcquisitionStage =
  | "PROPOSAL"
  | "IDENTIFICATION"
  | "SURVEY"
  | "VERIFICATION"
  | "NOTIFICATION"
  | "OBJECTION"
  | "AWARD"
  | "COMPENSATION"
  | "REHABILITATION_RESETTLEMENT"
  | "POSSESSION"
  | "CLOSURE";

export type AlertSeverity = "INFO" | "WARNING" | "CRITICAL";

export type DocumentType =
  | "NOTIFICATION"
  | "SURVEY_REPORT"
  | "OWNERSHIP_RECORD"
  | "AWARD_ORDER"
  | "COMPENSATION_RECEIPT"
  | "RR_PLAN"
  | "POSSESSION_ORDER"
  | "MAP"
  | "OTHER";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

// ── Core Models ────────────────────────────────────────

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  state_scope: string | null;
  district_scope: string | null;
  is_active: boolean;
}

export interface Project {
  project_id: string;
  name: string;
  type: string;
  states: string[];
  districts: string[];
  land_required_ha: number;
  land_acquired_ha: number;
  target_date: string; // ISO date
  status: ProjectStatus;
  progress_pct: number;
  risk_score: number;
  risk_level?: string;
  total_parcels: number;
  acquired_parcels: number;
  pending_parcels: number;
  sla_breaches: number;
  created_at: string;
  updated_at: string;
}

export interface Parcel {
  parcel_id: string;
  project_id: string;
  survey_number: string;
  area_ha: number;
  owner_name: string;
  owner_reference?: string;
  current_stage: AcquisitionStage;
  status: ParcelStatus;
  risk_score: number;
  village: string;
  district: string;
  state: string;
  days_pending?: number;
  assigned_officer?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ParcelGeoJSON {
  type: "FeatureCollection";
  features: Array<{
    type: "Feature";
    geometry: {
      type: "Polygon" | "MultiPolygon";
      coordinates: number[][][];
    };
    properties: Parcel;
  }>;
}

export interface StageRecord {
  stage_id: string;
  parcel_id: string;
  stage_name: AcquisitionStage;
  stage_order: number;
  start_date: string | null;
  target_date: string | null;
  completion_date: string | null;
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "SKIPPED";
  assigned_officer: string | null;
  remarks: string | null;
}

export interface Compensation {
  compensation_id: string;
  parcel_id: string;
  assessed_amount: number;
  approved_amount: number | null;
  paid_amount: number | null;
  payment_status: "PENDING" | "APPROVED" | "PAID" | "DISPUTED";
  payment_date: string | null;
}

export interface RRRecord {
  rr_id: string;
  parcel_id: string;
  beneficiary_name: string;
  affected_type: "DISPLACED" | "AFFECTED";
  rehabilitation_status: "PENDING" | "IN_PROGRESS" | "COMPLETED";
  entitlements: string;
}

export interface DocumentRecord {
  document_id: string;
  entity_id: string;
  entity_type: string;
  document_type: DocumentType;
  filename: string;
  file_path: string;
  file_hash: string;
  version: number;
  uploaded_by: string;
  uploaded_at: string;
}

export interface Alert {
  alert_id: string;
  user_id: string;
  alert_type: string;
  severity: AlertSeverity;
  entity_id: string;
  entity_type: string;
  message: string;
  is_read: boolean;
  created_at: string;
}

export interface AuditLogEntry {
  log_id: string;
  user_id: string;
  username: string;
  action: string;
  entity_type: string;
  entity_id: string;
  previous_state: Record<string, unknown> | null;
  new_state: Record<string, unknown> | null;
  ip_address: string;
  created_at: string;
}

// ── Dashboard Types ────────────────────────────────────

export interface NationalDashboard {
  active_projects: number;
  total_land_ha: number;
  acquired_pct: number;
  total_parcels: number;
  pending_cases: number;
  high_risk_projects: number;
  sla_breaches: number;
  stage_distribution: Record<AcquisitionStage, number>;
  compensation_summary: {
    assessed: number;
    approved: number;
    paid: number;
  };
  state_summary: Array<{
    state: string;
    projects: number;
    land_ha: number;
    acquired_pct: number;
    risk_level: RiskLevel;
    sla_breaches: number;
  }>;
  high_risk_project_list: Project[];
  user_scope?: {
    role: string;
    state?: string | null;
    district?: string | null;
    title: string;
  };
  quarterly_progress?: Array<{
    quarter: string;
    target_ha: number;
    acquired_ha: number;
  }>;
}

export interface ProjectSummary {
  project_id: string;
  total_parcels: number;
  acquired_parcels: number;
  pending_parcels: number;
  stage_distribution: Record<AcquisitionStage, number>;
  compensation: {
    assessed: number;
    approved: number;
    paid: number;
    pending: number;
  };
  rr: {
    total_families: number;
    displaced: number;
    rehabilitated: number;
    pending: number;
  };
  sla_breaches: number;
  possession: {
    possessed: number;
    pending: number;
  };
}

// ── Analytics Types ────────────────────────────────────

export interface DelayRiskResult {
  project_id: string;
  risk_score: number; // 0.0 - 1.0
  risk_level: RiskLevel;
  confidence: number; // 0.0 - 1.0
  snapshots_used: number;
  insufficient_data: boolean;
  feature_importance: Array<{
    feature: string;
    label: string; // Human-readable
    importance: number; // SHAP value
    direction: "positive" | "negative";
  }>;
}

export interface BottleneckResult {
  project_id: string;
  primary_bottleneck: {
    stage: AcquisitionStage;
    pending_count: number;
    avg_days_pending: number;
    sla_days: number;
    breach_rate: number;
    impact_description: string;
  };
  all_stages: Array<{
    stage: AcquisitionStage;
    pending_count: number;
    avg_days_pending: number;
    bottleneck_score: number;
  }>;
}

export interface PriorityCase {
  parcel_id: string;
  survey_number: string;
  stage: AcquisitionStage;
  days_pending: number;
  impact: RiskLevel;
  priority_score: number;
  recommendation: string;
}

export interface WhyDelayed {
  parcel_id: string;
  factors: Array<{
    factor: string;
    description: string;
    weight: number; // 0.0 - 1.0
  }>;
  summary: string;
}

// ── Pagination ─────────────────────────────────────────

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  limit: number;
  data: T[];
  items?: T[];
}

// ── Auth Types ─────────────────────────────────────────

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  user: User;
}

// ── API Error ──────────────────────────────────────────

export interface ApiError {
  detail: {
    code: string;
    message: string;
    timestamp: string;
  };
}

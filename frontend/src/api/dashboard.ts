import type { NationalDashboard } from "@/types/api";

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === "true";

// ── Mock Dashboard Data ────────────────────────────────
const MOCK_NATIONAL_DASHBOARD: NationalDashboard = {
  active_projects: 1248,
  total_land_ha: 45200,
  acquired_pct: 68.4,
  total_parcels: 45200,
  pending_cases: 3402,
  high_risk_projects: 18,
  sla_breaches: 42,
  stage_distribution: {
    PROPOSAL: 2100,
    IDENTIFICATION: 3400,
    SURVEY: 5200,
    VERIFICATION: 8900,
    NOTIFICATION: 6100,
    OBJECTION: 4200,
    AWARD: 5800,
    COMPENSATION: 4300,
    REHABILITATION_RESETTLEMENT: 2800,
    POSSESSION: 1600,
    CLOSURE: 800,
  },
  compensation_summary: {
    assessed: 12500_00_00_000, // ₹12,500 Cr
    approved: 9800_00_00_000,
    paid: 7200_00_00_000,
  },
  state_summary: [
    {
      state: "Maharashtra",
      projects: 186,
      land_ha: 8400,
      acquired_pct: 72,
      risk_level: "MEDIUM",
      sla_breaches: 8,
    },
    {
      state: "Uttar Pradesh",
      projects: 142,
      land_ha: 7200,
      acquired_pct: 58,
      risk_level: "HIGH",
      sla_breaches: 12,
    },
    {
      state: "Karnataka",
      projects: 98,
      land_ha: 5100,
      acquired_pct: 81,
      risk_level: "LOW",
      sla_breaches: 3,
    },
    {
      state: "Gujarat",
      projects: 120,
      land_ha: 6300,
      acquired_pct: 65,
      risk_level: "MEDIUM",
      sla_breaches: 7,
    },
    {
      state: "Tamil Nadu",
      projects: 88,
      land_ha: 4200,
      acquired_pct: 75,
      risk_level: "LOW",
      sla_breaches: 2,
    },
    {
      state: "Rajasthan",
      projects: 76,
      land_ha: 5800,
      acquired_pct: 52,
      risk_level: "HIGH",
      sla_breaches: 10,
    },
    {
      state: "Madhya Pradesh",
      projects: 95,
      land_ha: 4600,
      acquired_pct: 69,
      risk_level: "MEDIUM",
      sla_breaches: 5,
    },
    {
      state: "Telangana",
      projects: 64,
      land_ha: 3100,
      acquired_pct: 88,
      risk_level: "LOW",
      sla_breaches: 1,
    },
  ],
  high_risk_project_list: [],
};

// Quarterly acquisition progress (for chart)
export interface QuarterlyProgress {
  quarter: string;
  acquired: number;
  pending: number;
  target: number;
}

const MOCK_QUARTERLY_PROGRESS: QuarterlyProgress[] = [
  { quarter: "Q1 2025", acquired: 8200, pending: 12400, target: 11000 },
  { quarter: "Q2 2025", acquired: 14800, pending: 10800, target: 16000 },
  { quarter: "Q3 2025", acquired: 22400, pending: 8200, target: 21000 },
  { quarter: "Q4 2025", acquired: 30800, pending: 5600, target: 28000 },
];

// Recent critical alerts (for dashboard table)
export interface DashboardAlert {
  id: string;
  project_name: string;
  issue_type: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM";
  time_ago: string;
}

const MOCK_ALERTS: DashboardAlert[] = [
  {
    id: "a-001",
    project_name: "NH-48 Expansion Sector 9",
    issue_type: "Legal Dispute - Landowner",
    severity: "CRITICAL",
    time_ago: "10 mins ago",
  },
  {
    id: "a-002",
    project_name: "Mumbai-Ahmedabad HSR",
    issue_type: "Compensation Delay > 30 Days",
    severity: "HIGH",
    time_ago: "1 hr ago",
  },
  {
    id: "a-003",
    project_name: "Eastern Dedicated Freight Corridor",
    issue_type: "Survey Boundary Mismatch",
    severity: "MEDIUM",
    time_ago: "3 hrs ago",
  },
  {
    id: "a-004",
    project_name: "Kochi Metro Phase II",
    issue_type: "Environmental Clearance Pending",
    severity: "HIGH",
    time_ago: "5 hrs ago",
  },
  {
    id: "a-005",
    project_name: "Delhi-Meerut RRTS",
    issue_type: "SLA Breach - Verification Stage",
    severity: "CRITICAL",
    time_ago: "6 hrs ago",
  },
];

// Bottleneck stage breakdown (for horizontal bars)
export interface StageBreakdown {
  stage: string;
  percentage: number;
  count: number;
}

const MOCK_STAGE_BREAKDOWN: StageBreakdown[] = [
  { stage: "Survey & Demarcation", percentage: 35, count: 8900 },
  { stage: "Valuation", percentage: 28, count: 5800 },
  { stage: "Compensation Disbursement", percentage: 18, count: 4300 },
  { stage: "Proposal Phase", percentage: 12, count: 2100 },
  { stage: "Possession", percentage: 7, count: 1600 },
];

// ── API Functions ──────────────────────────────────────

async function mockDelay(ms = 500): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function fetchNationalDashboard(): Promise<NationalDashboard> {
  if (USE_MOCKS) {
    await mockDelay();
    return MOCK_NATIONAL_DASHBOARD;
  }
  const { default: apiClient } = await import("./client");
  const response = await apiClient.get<NationalDashboard>("/dashboard/national");
  return response.data;
}

export async function fetchQuarterlyProgress(): Promise<QuarterlyProgress[]> {
  if (USE_MOCKS) {
    await mockDelay(300);
    return MOCK_QUARTERLY_PROGRESS;
  }
  const { default: apiClient } = await import("./client");
  const response = await apiClient.get<QuarterlyProgress[]>("/dashboard/progress");
  return response.data;
}

export async function fetchDashboardAlerts(): Promise<DashboardAlert[]> {
  if (USE_MOCKS) {
    await mockDelay(400);
    return MOCK_ALERTS;
  }
  const { default: apiClient } = await import("./client");
  const response = await apiClient.get<DashboardAlert[]>("/alerts?severity=CRITICAL,HIGH&limit=5");
  return response.data;
}

export async function fetchStageBreakdown(): Promise<StageBreakdown[]> {
  if (USE_MOCKS) {
    await mockDelay(300);
    return MOCK_STAGE_BREAKDOWN;
  }
  const { default: apiClient } = await import("./client");
  const response = await apiClient.get<StageBreakdown[]>("/dashboard/stages");
  return response.data;
}

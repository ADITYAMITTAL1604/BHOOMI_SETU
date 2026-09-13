import apiClient from "./client";

export interface ExecutiveSummaryReport {
  report_title: string;
  generated_at: string;
  project: {
    project_id?: string;
    name: string;
    type?: string;
    status: string;
    states?: string[];
    districts?: string[];
  };
  metrics: {
    total_parcels: number;
    total_parcel_area_ha: number;
    land_required_ha: number;
    land_acquired_ha: number;
    progress_pct: number;
    avg_risk_score: number;
  };
  stages: Record<string, number>;
  compensation: {
    approved_amount: number;
    paid_amount: number;
    pending_amount: number;
    disbursement_pct: number;
  };
  rehabilitation: {
    total_affected_families: number;
  };
}

export async function fetchExecutiveSummary(
  paramsOrProjectId?: string | { project_id?: string; state?: string; district?: string }
): Promise<ExecutiveSummaryReport> {
  const params =
    typeof paramsOrProjectId === "string"
      ? { project_id: paramsOrProjectId }
      : paramsOrProjectId || {};

  const response = await apiClient.get<ExecutiveSummaryReport>("/reports/executive-summary", {
    params: {
      project_id: params.project_id || undefined,
      state: params.state || undefined,
      district: params.district || undefined,
      format: "json",
    },
  });
  return response.data;
}

export function getExecutiveSummaryHtmlUrl(projectId?: string): string {
  const base = apiClient.defaults.baseURL || "/api/v1";
  const params = new URLSearchParams({ format: "html" });
  if (projectId) params.append("project_id", projectId);
  return `${base}/reports/executive-summary?${params.toString()}`;
}

export interface ReportKPIs {
  total_parcels: number;
  completed_parcels: number;
  in_progress_parcels: number;
  blocked_parcels: number;
  disputed_parcels: number;
  total_area_ha: number;
  completion_pct: number;
  total_projects: number;
  compensation: {
    assessed: number;
    approved: number;
    paid: number;
    pending: number;
    disbursement_pct: number;
  };
}

export async function fetchKPIs(params?: {
  state?: string;
  district?: string;
  project_id?: string;
}): Promise<ReportKPIs> {
  const response = await apiClient.get<ReportKPIs>("/reports/kpis", { params });
  return response.data;
}

export function getExcelExportUrl(params?: {
  state?: string;
  district?: string;
  project_id?: string;
  stage?: string;
  status?: string;
}): string {
  const base = apiClient.defaults.baseURL || "/api/v1";
  const searchParams = new URLSearchParams();
  if (params?.state) searchParams.append("state", params.state);
  if (params?.district) searchParams.append("district", params.district);
  if (params?.project_id) searchParams.append("project_id", params.project_id);
  if (params?.stage) searchParams.append("stage", params.stage);
  if (params?.status) searchParams.append("status", params.status);
  return `${base}/reports/export/excel?${searchParams.toString()}`;
}


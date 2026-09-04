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

export async function fetchExecutiveSummary(projectId?: string): Promise<ExecutiveSummaryReport> {
  const response = await apiClient.get<ExecutiveSummaryReport>("/reports/executive-summary", {
    params: {
      project_id: projectId || undefined,
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

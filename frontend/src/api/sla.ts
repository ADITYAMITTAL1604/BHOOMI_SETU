import apiClient from "./client";
import type {
  SLADashboardData,
  SLAStageDelay,
  SLADistrictDelay,
  SLAProjectDelay,
} from "@/types/api";

export async function getSLADashboard(params?: {
  state?: string;
  district?: string;
  project_id?: string;
}): Promise<SLADashboardData> {
  const response = await apiClient.get<any>("/sla/dashboard", { params });
  const raw = response.data;

  // Backend returns { summary: { total_active_stages, ok, warning, critical, breach_rate }, stage_breakdown }
  // Frontend expects { total_parcels, on_track, at_risk, breached, overall_compliance_pct, avg_days_pending }
  if (raw?.summary) {
    const s = raw.summary;
    const total = s.total_active_stages || 0;
    const ok = s.ok || 0;
    const warning = s.warning || 0;
    const critical = s.critical || 0;
    const compliancePct = total > 0 ? Math.round(((ok + warning) / total) * 100 * 10) / 10 : 100;

    // Compute avg_days_pending from stage_breakdown if available
    let avgDays = 0;
    const breakdown = raw.stage_breakdown || [];
    if (breakdown.length > 0) {
      const totalDays = breakdown.reduce((sum: number, b: any) => sum + (b.avg_days_pending || 0) * (b.total || 1), 0);
      const totalCount = breakdown.reduce((sum: number, b: any) => sum + (b.total || 0), 0);
      avgDays = totalCount > 0 ? Math.round(totalDays / totalCount * 10) / 10 : 0;
    }

    return {
      total_parcels: total,
      on_track: ok,
      at_risk: warning,
      breached: critical,
      overall_compliance_pct: compliancePct,
      avg_days_pending: avgDays,
    };
  }

  // If already in correct format, pass through
  return raw as SLADashboardData;
}

export async function getStageDelays(params?: {
  state?: string;
  district?: string;
  project_id?: string;
}): Promise<SLAStageDelay[]> {
  const response = await apiClient.get<any>("/sla/stage-delays", { params });
  const raw = response.data;

  // Backend returns { delays: [...] } with shape { stage_name, sla_days, total_parcels, breached_parcels, ... }
  const items: any[] = raw?.delays || (Array.isArray(raw) ? raw : raw?.items || []);

  return items.map((d: any) => ({
    stage: d.stage_name || d.stage,
    sla_days: d.sla_days || 0,
    total_parcels: d.total_parcels || 0,
    breached_count: d.breached_parcels ?? d.breached_count ?? 0,
    breach_rate: d.breach_rate || 0,
    avg_days_pending: d.avg_days_pending || 0,
    max_days_pending: d.max_days_pending || 0,
  }));
}

export async function getDistrictDelays(params?: {
  state?: string;
  project_id?: string;
}): Promise<SLADistrictDelay[]> {
  const response = await apiClient.get<any>("/sla/district-delays", { params });
  const raw = response.data;

  // Backend returns { districts: [...] } with shape { state, district, total_stages, breached, warning, ok, ... }
  const items: any[] = raw?.districts || (Array.isArray(raw) ? raw : raw?.items || []);

  return items.map((d: any) => ({
    district: d.district || "",
    state: d.state || "",
    total_parcels: d.total_stages || d.total_parcels || 0,
    breached_count: d.breached ?? d.breached_count ?? 0,
    breach_rate: d.breach_rate || 0,
    avg_days_pending: d.avg_days_pending || 0,
  }));
}

export async function getProjectDelays(params?: {
  state?: string;
  district?: string;
}): Promise<SLAProjectDelay[]> {
  const response = await apiClient.get<any>("/sla/project-delays", { params });
  const raw = response.data;

  // Backend returns { projects: [...] } with shape { project_id, project_name, total_stages, breached, ... }
  const items: any[] = raw?.projects || (Array.isArray(raw) ? raw : raw?.items || []);

  return items.map((p: any) => ({
    project_id: p.project_id || "",
    project_name: p.project_name || "",
    total_parcels: p.total_stages || p.total_parcels || 0,
    breached_count: p.breached ?? p.breached_count ?? 0,
    breach_rate: p.breach_rate || 0,
    worst_stage: p.worst_stage || "",
    avg_days_overdue: p.avg_days_pending || p.avg_days_overdue || 0,
  }));
}

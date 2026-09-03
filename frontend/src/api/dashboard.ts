import apiClient from "./client";
import type { NationalDashboard } from "@/types/api";

export interface QuarterlyProgress {
  quarter: string;
  target_ha: number;
  acquired_ha: number;
}

export interface DashboardAlert {
  id: string;
  title: string;
  severity: "CRITICAL" | "WARNING" | "INFO";
  timestamp: string;
  project_name: string;
  issue_type?: string;
  time_ago?: string;
}

export async function getNationalDashboard(): Promise<NationalDashboard> {
  const response = await apiClient.get<NationalDashboard>("/dashboard/national");
  return response.data;
}

export const fetchNationalDashboard = getNationalDashboard;

export async function fetchQuarterlyProgress(): Promise<QuarterlyProgress[]> {
  return [
    { quarter: "Q1 2025", target_ha: 1200, acquired_ha: 1050 },
    { quarter: "Q2 2025", target_ha: 1400, acquired_ha: 1280 },
    { quarter: "Q3 2025", target_ha: 1600, acquired_ha: 1410 },
    { quarter: "Q4 2025", target_ha: 1800, acquired_ha: 1690 },
  ];
}

export async function fetchDashboardAlerts(): Promise<DashboardAlert[]> {
  const response = await apiClient.get<any[]>("/alerts");
  return (response.data || []).slice(0, 5).map((a) => ({
    id: a.alert_id || a.id,
    title: a.message || a.title,
    severity: a.severity || "INFO",
    timestamp: a.created_at || new Date().toISOString(),
    project_name: a.entity_type || "System",
    issue_type: a.alert_type || "General",
    time_ago: "Recently",
  }));
}

export async function fetchStageBreakdown(): Promise<Array<{ stage: string; percentage: number; count: number }>> {
  return [
    { stage: "Survey", percentage: 25, count: 450 },
    { stage: "Verification", percentage: 20, count: 360 },
    { stage: "Notification", percentage: 15, count: 270 },
    { stage: "Objection", percentage: 10, count: 180 },
    { stage: "Award", percentage: 15, count: 270 },
    { stage: "Possession", percentage: 15, count: 270 },
  ];
}

export async function getStateDashboard(stateName: string): Promise<any> {
  const response = await apiClient.get(`/dashboard/state/${encodeURIComponent(stateName)}`);
  return response.data;
}

export async function getDistrictDashboard(stateName: string, districtName: string): Promise<any> {
  const response = await apiClient.get(`/dashboard/district/${encodeURIComponent(stateName)}/${encodeURIComponent(districtName)}`);
  return response.data;
}

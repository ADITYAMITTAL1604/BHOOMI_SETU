import apiClient from "./client";
import type { DelayRiskResult, BottleneckResult, PriorityCase, WhyDelayed } from "@/types/api";

export async function getProjectDelayRisk(projectId?: string): Promise<DelayRiskResult> {
  const targetId = projectId || "default";
  const response = await apiClient.get<DelayRiskResult>(`/analytics/projects/${targetId}/delay-risk`);
  return response.data;
}

export const fetchDelayRisk = getProjectDelayRisk;

export async function getProjectBottlenecks(projectId?: string): Promise<BottleneckResult> {
  const targetId = projectId || "default";
  const response = await apiClient.get<BottleneckResult>(`/analytics/projects/${targetId}/bottlenecks`);
  return response.data;
}

export const fetchBottleneckAnalysis = getProjectBottlenecks;

export async function getPriorityCases(projectId?: string): Promise<PriorityCase[]> {
  const targetId = projectId || "default";
  const response = await apiClient.get<PriorityCase[] | { ranked_parcels: PriorityCase[] }>(`/analytics/priority/${targetId}`);
  const resData = response.data as any;
  if (Array.isArray(resData)) return resData;
  if (resData && Array.isArray(resData.ranked_parcels)) return resData.ranked_parcels;
  return [];
}

export const fetchPriorityCases = getPriorityCases;

export async function getWhyDelayed(parcelId: string): Promise<WhyDelayed> {
  const response = await apiClient.get<WhyDelayed>(`/analytics/parcels/${parcelId}/why-delayed`);
  return response.data;
}

import apiClient from "./client";
import type { Project, ProjectSummary, PaginatedResponse } from "@/types/api";

export interface GetProjectsParams {
  state?: string;
  district?: string;
  type?: string;
  status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: string;
  page?: number;
  limit?: number;
}

export async function getProjects(params: GetProjectsParams = {}): Promise<PaginatedResponse<Project>> {
  const response = await apiClient.get<PaginatedResponse<Project> | { items: Project[]; total: number; page: number; size: number }>("/projects", {
    params: {
      state: params.state,
      district: params.district,
      type: params.type,
      status: params.status,
      q: params.search,
      sort_by: params.sort_by,
      sort_order: params.sort_order,
      page: params.page || 1,
      page_size: params.limit || 10,
    },
  });

  const resData = response.data as any;
  if ("items" in resData) {
    return {
      data: resData.items,
      total: resData.total,
      page: resData.page,
      limit: resData.size,
    };
  }
  return resData;
}

export const listProjects = getProjects;
export const getProject = getProjectById;

export async function getProjectDistricts(): Promise<string[]> {
  const response = await apiClient.get<string[]>("/projects/districts/list");
  return response.data || [];
}

export async function getProjectById(projectId: string): Promise<Project> {
  const response = await apiClient.get<Project>(`/projects/${projectId}`);
  return response.data;
}

export async function getProjectSummary(projectId: string): Promise<ProjectSummary> {
  const response = await apiClient.get<ProjectSummary>(`/projects/${projectId}/summary`);
  return response.data;
}

export async function getRecentActivities(projectId: string): Promise<any[]> {
  const response = await apiClient.get<any>(`/projects/${projectId}/timeline`);
  const data = response.data;
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.timeline)) {
    return data.timeline.map((evt: any) => ({
      id: evt.event_id || Math.random().toString(),
      user: evt.actor_id || "Competent Authority",
      action: evt.title || evt.event_type || "Updated milestone",
      entity: evt.description || "",
      time_ago: evt.timestamp
        ? new Date(evt.timestamp).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric",
          })
        : "Recently",
      icon_color: evt.icon_color || "bg-[#D47A22]",
    }));
  }
  return [];
}

export async function createProject(projectData: Partial<Project>): Promise<Project> {
  const response = await apiClient.post<Project>("/projects", projectData);
  return response.data;
}

export async function updateProject(projectId: string, projectData: Partial<Project>): Promise<Project> {
  const response = await apiClient.put<Project>(`/projects/${projectId}`, projectData);
  return response.data;
}

export async function downloadProjectsCsv(params: {
  search?: string;
  state?: string;
  district?: string;
  sort_by?: string;
  sort_order?: string;
} = {}): Promise<void> {
  const response = await apiClient.get("/projects/export/csv", {
    params: {
      search: params.search || undefined,
      state: params.state && params.state !== "All States" ? params.state : undefined,
      district: params.district && params.district !== "All Districts" ? params.district : undefined,
      sort_by: params.sort_by,
      sort_order: params.sort_order,
    },
    responseType: "blob",
  });

  const blob = new Blob([response.data], { type: "text/csv;charset=utf-8;" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  const dateStr = new Date().toISOString().slice(0, 10);
  link.setAttribute("download", `BhoomiSetu_Projects_Inventory_${dateStr}.csv`);
  document.body.appendChild(link);
  link.click();
  link.parentNode?.removeChild(link);
  window.URL.revokeObjectURL(url);
}


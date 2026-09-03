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

export async function getProjectById(projectId: string): Promise<Project> {
  const response = await apiClient.get<Project>(`/projects/${projectId}`);
  return response.data;
}

export async function getProjectSummary(projectId: string): Promise<ProjectSummary> {
  const response = await apiClient.get<ProjectSummary>(`/projects/${projectId}/summary`);
  return response.data;
}

export async function getRecentActivities(projectId: string): Promise<any[]> {
  const response = await apiClient.get<any[]>(`/projects/${projectId}/timeline`);
  return response.data || [];
}

export async function createProject(projectData: Partial<Project>): Promise<Project> {
  const response = await apiClient.post<Project>("/projects", projectData);
  return response.data;
}

export async function updateProject(projectId: string, projectData: Partial<Project>): Promise<Project> {
  const response = await apiClient.put<Project>(`/projects/${projectId}`, projectData);
  return response.data;
}

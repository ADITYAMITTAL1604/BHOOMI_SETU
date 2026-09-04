import apiClient from "./client";
import type { ParcelGeoJSON } from "@/types/api";

export async function getProjectGeoJSON(projectId?: string): Promise<ParcelGeoJSON> {
  const targetId = projectId || "all";
  const response = await apiClient.get<ParcelGeoJSON>(`/gis/projects/${targetId}/geojson`);
  return response.data;
}

export const fetchGISParcels = getProjectGeoJSON;

export async function fetchParcelList(projectId?: string): Promise<any[]> {
  const params: Record<string, any> = { page_size: 100 };
  if (projectId) params.project_id = projectId;
  const response = await apiClient.get<{ items: any[] } | any[]>(`/parcels`, { params });
  const data = response.data as any;
  if ("items" in data) return data.items;
  if (Array.isArray(data)) return data;
  return [];
}

export async function getBoundaries(level: "state" | "district" | "village", name?: string): Promise<any> {
  const response = await apiClient.get(`/gis/boundaries`, {
    params: { level, name },
  });
  return response.data;
}

export async function searchSpatial(bbox: [number, number, number, number]): Promise<ParcelGeoJSON> {
  const response = await apiClient.get<ParcelGeoJSON>(`/gis/spatial-search`, {
    params: { bbox: bbox.join(",") },
  });
  return response.data;
}

import apiClient from "./client";
import type { Parcel, StageRecord, Compensation, RRRecord, PaginatedResponse } from "@/types/api";

export interface GetParcelsParams {
  project_id?: string;
  stage?: string;
  status?: string;
  search?: string;
  page?: number;
  limit?: number;
}

export async function getParcels(params: GetParcelsParams = {}): Promise<PaginatedResponse<Parcel>> {
  const response = await apiClient.get<PaginatedResponse<Parcel> | { items: Parcel[]; total: number; page: number; size: number }>("/parcels", {
    params: {
      project_id: params.project_id,
      stage: params.stage,
      status: params.status,
      q: params.search,
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

export async function getParcelById(parcelId: string): Promise<Parcel & { stages?: StageRecord[]; compensation?: Compensation; rr?: RRRecord }> {
  const response = await apiClient.get(`/parcels/${parcelId}`);
  return response.data;
}

export async function updateParcelStage(parcelId: string, stageData: { stage_name: string; remarks?: string }): Promise<Parcel> {
  const response = await apiClient.post<Parcel>(`/parcels/${parcelId}/stage`, stageData);
  return response.data;
}

export async function updateParcel(parcelId: string, parcelData: Partial<Parcel>): Promise<Parcel> {
  const response = await apiClient.put<Parcel>(`/parcels/${parcelId}`, parcelData);
  return response.data;
}

import apiClient from "./client";
import type { ApprovalQueueItem, DocumentApproval } from "@/types/api";

export async function getApprovalQueue(params?: {
  status?: string;
  skip?: number;
  limit?: number;
}): Promise<ApprovalQueueItem[]> {
  const response = await apiClient.get<any>("/approvals/queue", { params });
  if (Array.isArray(response.data)) return response.data;
  if (response.data?.items) return response.data.items;
  if (response.data?.data) return response.data.data;
  return [];
}

export async function getPendingApprovals(): Promise<ApprovalQueueItem[]> {
  const response = await apiClient.get<any>("/approvals/pending");
  if (Array.isArray(response.data)) return response.data;
  if (response.data?.items) return response.data.items;
  return [];
}

export async function approveDocument(
  documentId: string,
  remarks?: string
): Promise<DocumentApproval> {
  const response = await apiClient.post<DocumentApproval>(
    `/approvals/${documentId}/approve`,
    { remarks }
  );
  return response.data;
}

export async function rejectDocument(
  documentId: string,
  remarks: string
): Promise<DocumentApproval> {
  const response = await apiClient.post<DocumentApproval>(
    `/approvals/${documentId}/reject`,
    { remarks }
  );
  return response.data;
}

export async function requestRevision(
  documentId: string,
  remarks: string
): Promise<DocumentApproval> {
  const response = await apiClient.post<DocumentApproval>(
    `/approvals/${documentId}/revise`,
    { remarks }
  );
  return response.data;
}

export async function getApprovalHistory(
  documentId: string
): Promise<DocumentApproval[]> {
  const response = await apiClient.get<DocumentApproval[]>(
    `/approvals/${documentId}/history`
  );
  return Array.isArray(response.data) ? response.data : [];
}

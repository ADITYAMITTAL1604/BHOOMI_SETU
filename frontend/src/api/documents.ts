import apiClient from "./client";
import type { DocumentRecord } from "@/types/api";

export async function getDocuments(entityId?: string, entityType?: string): Promise<DocumentRecord[]> {
  const response = await apiClient.get<DocumentRecord[]>("/documents", {
    params: { entity_id: entityId, entity_type: entityType },
  });
  return response.data;
}

export async function uploadDocument(formData: FormData): Promise<DocumentRecord> {
  const response = await apiClient.post<DocumentRecord>("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<{ success: boolean }> {
  const response = await apiClient.delete<{ success: boolean }>(`/documents/${documentId}`);
  return response.data;
}

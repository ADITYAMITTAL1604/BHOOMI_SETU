import apiClient from "./client";

export interface DocumentItem {
  document_id: string;
  title: string;
  description?: string;
  document_type: string;
  mime_type: string;
  file_size_bytes: number;
  file_path?: string;
  version: number;
  is_verified: boolean;
  approval_status: string;
  current_approval_step: number;
  uploaded_by?: string;
  uploaded_by_name?: string;
  sha256?: string;
  file_hash?: string;
  project_id?: string;
  project_name?: string;
  parcel_id?: string;
  parcel_survey_number?: string;
  created_at?: string;
  updated_at?: string;
}

export interface GetDocumentsParams {
  project_id?: string;
  parcel_id?: string;
  document_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}

export async function getDocuments(params?: GetDocumentsParams): Promise<DocumentItem[]> {
  const response = await apiClient.get<any>("/documents", { params });
  if (Array.isArray(response.data)) return response.data;
  if (response.data?.items && Array.isArray(response.data.items)) return response.data.items;
  if (response.data?.data && Array.isArray(response.data.data)) return response.data.data;
  return [];
}

export async function getDocumentDetails(documentId: string): Promise<DocumentItem> {
  const response = await apiClient.get<DocumentItem>(`/documents/${documentId}`);
  return response.data;
}

export async function uploadDocument(formData: FormData): Promise<DocumentItem> {
  const response = await apiClient.post<DocumentItem>("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function deleteDocument(documentId: string): Promise<void> {
  await apiClient.delete(`/documents/${documentId}`);
}

export interface DocumentPreview extends DocumentItem {
  text_content: string;
  parcel_info?: string;
}

export async function getDocumentPreview(documentId: string): Promise<DocumentPreview> {
  const response = await apiClient.get<DocumentPreview>(`/documents/${documentId}/preview`);
  return response.data;
}

export async function downloadDocumentFile(
  documentId: string,
  filename?: string,
  format: "pdf" | "docx" | "xlsx" | "txt" = "pdf"
): Promise<void> {
  const response = await apiClient.get(`/documents/${documentId}/download`, {
    params: { format },
    responseType: "blob",
  });
  
  const ext = format;
  const cleanTitle = filename ? filename.replace(/\.[^/.]+$/, "").replace(/[^a-zA-Z0-9_-]/g, "_") : `document_${documentId}`;
  const downloadName = `${cleanTitle}.${ext}`;

  const contentType = (response.headers?.["content-type"] as string) || "application/octet-stream";
  const blob = new Blob([response.data], { type: contentType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", downloadName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}


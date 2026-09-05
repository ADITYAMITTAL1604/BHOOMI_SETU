import apiClient from "./client";
import type { Alert } from "@/types/api";

export async function getAlerts(unreadOnly = false): Promise<Alert[]> {
  const response = await apiClient.get<any>("/alerts", {
    params: { is_read: unreadOnly ? false : undefined },
  });
  
  if (Array.isArray(response.data)) return response.data;
  if (response.data && Array.isArray(response.data.items)) return response.data.items;
  if (response.data && Array.isArray(response.data.data)) return response.data.data;
  
  return [];
}

export async function markAlertAsRead(alertId: string): Promise<Alert> {
  const response = await apiClient.put<Alert>(`/alerts/${alertId}/read`);
  return response.data;
}

export async function markAllAlertsAsRead(): Promise<{ message: string }> {
  const response = await apiClient.put<{ message: string }>("/alerts/read-all");
  return response.data;
}

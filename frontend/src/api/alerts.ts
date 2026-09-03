import apiClient from "./client";
import type { Alert } from "@/types/api";

export async function getAlerts(unreadOnly = false): Promise<Alert[]> {
  const response = await apiClient.get<Alert[]>("/alerts", {
    params: { unread_only: unreadOnly },
  });
  return response.data;
}

export async function markAlertAsRead(alertId: string): Promise<Alert> {
  const response = await apiClient.put<Alert>(`/alerts/${alertId}/read`);
  return response.data;
}

export async function markAllAlertsAsRead(): Promise<{ message: string }> {
  const response = await apiClient.put<{ message: string }>("/alerts/read-all");
  return response.data;
}

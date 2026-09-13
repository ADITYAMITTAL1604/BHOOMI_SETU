import apiClient from "./client";
import type { AppNotification } from "@/types/api";

export async function getNotifications(params?: {
  category?: string;
  skip?: number;
  limit?: number;
}): Promise<AppNotification[]> {
  const response = await apiClient.get<any>("/notifications", { params });
  if (Array.isArray(response.data)) return response.data;
  if (response.data?.items) return response.data.items;
  if (response.data?.data) return response.data.data;
  return [];
}

export async function getUnreadCount(): Promise<number> {
  const response = await apiClient.get<any>("/notifications/unread-count");
  return response.data?.count ?? response.data?.unread_count ?? 0;
}

export async function markNotificationRead(
  notificationId: string
): Promise<AppNotification> {
  const response = await apiClient.put<AppNotification>(
    `/notifications/${notificationId}/read`
  );
  return response.data;
}

export async function markAllNotificationsRead(): Promise<{ message: string }> {
  const response = await apiClient.put<{ message: string }>(
    "/notifications/read-all"
  );
  return response.data;
}

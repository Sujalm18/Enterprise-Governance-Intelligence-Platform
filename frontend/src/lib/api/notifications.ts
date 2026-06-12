import { endpoints } from "@/lib/api/endpoints";
import { request } from "@/lib/api/client";
import type {
  NotificationResponse,
  InboxResponse,
} from "@/types/api";

export function listNotifications(): Promise<NotificationResponse[]> {
  return request<NotificationResponse[]>({
    method: "GET",
    url: endpoints.notifications,
  });
}

export function readNotification(
  id: number | string,
  readStatus: boolean = true,
): Promise<NotificationResponse> {
  return request<NotificationResponse>({
    method: "PUT",
    url: endpoints.readNotification(id),
    data: { read_status: readStatus },
  });
}

export function readAllNotifications(): Promise<{ message: string }> {
  return request<{ message: string }>({
    method: "PUT",
    url: endpoints.readAllNotifications,
  });
}

export function getInbox(): Promise<InboxResponse> {
  return request<InboxResponse>({
    method: "GET",
    url: endpoints.inbox,
  });
}

export function generateDemoData(
  size: "small" | "medium" | "enterprise",
): Promise<{ message: string; size: string }> {
  return request<{ message: string; size: string }>({
    method: "POST",
    url: endpoints.generateDemoData,
    data: { size },
  });
}

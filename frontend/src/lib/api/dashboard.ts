import { endpoints } from "@/lib/api/endpoints";
import { request } from "@/lib/api/client";
import type {
  DashboardChartsResponse,
  DashboardStatsResponse,
  HealthResponse,
} from "@/types/api";

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>({
    method: "GET",
    url: endpoints.health,
  });
}

export function getDashboardStats(): Promise<DashboardStatsResponse> {
  return request<DashboardStatsResponse>({
    method: "GET",
    url: endpoints.dashboardStats,
  });
}

export function getDashboardCharts(): Promise<DashboardChartsResponse> {
  return request<DashboardChartsResponse>({
    method: "GET",
    url: endpoints.dashboardCharts,
  });
}

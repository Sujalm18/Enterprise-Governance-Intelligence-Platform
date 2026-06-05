import { endpoints } from "@/lib/api/endpoints";
import { request } from "@/lib/api/client";
import type {
  EscalationItemResponse,
  EscalationRouteRequest,
  ListEscalationsParams,
} from "@/types/api";

export function listEscalations(
  params: ListEscalationsParams = {},
): Promise<EscalationItemResponse[]> {
  return request<EscalationItemResponse[]>({
    method: "GET",
    url: endpoints.escalations,
    params,
  });
}

export function routeEscalation(
  id: number | string,
  payload: EscalationRouteRequest,
): Promise<EscalationItemResponse> {
  return request<EscalationItemResponse>({
    method: "POST",
    url: endpoints.routeEscalation(id),
    data: payload,
  });
}

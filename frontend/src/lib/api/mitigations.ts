import { endpoints } from "@/lib/api/endpoints";
import { request } from "@/lib/api/client";
import type {
  MitigationTaskResponse,
  MitigationTaskUpdateRequest,
} from "@/types/api";

export function listMitigations(
  params: Record<string, any> = {},
): Promise<MitigationTaskResponse[]> {
  return request<MitigationTaskResponse[]>({
    method: "GET",
    url: endpoints.mitigations,
    params,
  });
}

export function getMitigation(
  id: number | string,
): Promise<MitigationTaskResponse> {
  return request<MitigationTaskResponse>({
    method: "GET",
    url: endpoints.mitigation(id),
  });
}

export function updateMitigation(
  id: number | string,
  payload: MitigationTaskUpdateRequest,
): Promise<MitigationTaskResponse> {
  return request<MitigationTaskResponse>({
    method: "PUT",
    url: endpoints.mitigation(id),
    data: payload,
  });
}

export function verifyMitigation(
  id: number | string,
): Promise<MitigationTaskResponse> {
  return request<MitigationTaskResponse>({
    method: "POST",
    url: endpoints.verifyMitigation(id),
  });
}

export function reopenMitigation(
  id: number | string,
): Promise<MitigationTaskResponse> {
  return request<MitigationTaskResponse>({
    method: "POST",
    url: endpoints.reopenMitigation(id),
  });
}

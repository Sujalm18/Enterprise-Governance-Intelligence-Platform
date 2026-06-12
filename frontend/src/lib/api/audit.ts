import { request } from "@/lib/api/client";
import type { AuditLogResponse } from "@/types/api";

export function getAuditEvents(): Promise<AuditLogResponse[]> {
  return request<AuditLogResponse[]>({
    method: "GET",
    url: "/api/governance/audit-events",
  });
}

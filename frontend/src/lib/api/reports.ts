import { endpoints } from "@/lib/api/endpoints";
import { request } from "@/lib/api/client";
import type {
  GovernanceReportResponse,
  ListReportsParams,
  WorkflowJobResponse,
} from "@/types/api";

export function listGovernanceReports(
  params: ListReportsParams = {},
): Promise<GovernanceReportResponse[]> {
  return request<GovernanceReportResponse[]>({
    method: "GET",
    url: endpoints.reports,
    params,
  });
}

export function getGovernanceReport(
  id: number | string,
): Promise<GovernanceReportResponse> {
  return request<GovernanceReportResponse>({
    method: "GET",
    url: endpoints.report(id),
  });
}

export function getWorkflowJob(id: number | string): Promise<WorkflowJobResponse> {
  return request<WorkflowJobResponse>({
    method: "GET",
    url: endpoints.workflowJob(id),
  });
}

export function assignGovernanceReport(
  id: number | string,
  assignedTo: string,
): Promise<GovernanceReportResponse> {
  return request<GovernanceReportResponse>({
    method: "PATCH",
    url: `${endpoints.reports}/${id}/assign`,
    data: { assigned_to: assignedTo },
  });
}

export function escalateGovernanceReport(
  id: number | string,
): Promise<GovernanceReportResponse> {
  return request<GovernanceReportResponse>({
    method: "PATCH",
    url: `${endpoints.reports}/${id}/escalate`,
  });
}

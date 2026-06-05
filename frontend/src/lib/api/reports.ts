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

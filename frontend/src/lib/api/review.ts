import { endpoints } from "@/lib/api/endpoints";
import { request } from "@/lib/api/client";
import type { GovernanceReportResponse, ReportReviewRequest } from "@/types/api";

export function reviewGovernanceReport(
  id: number | string,
  payload: ReportReviewRequest,
): Promise<GovernanceReportResponse> {
  return request<GovernanceReportResponse>({
    method: "PATCH",
    url: endpoints.reviewReport(id),
    data: payload,
  });
}

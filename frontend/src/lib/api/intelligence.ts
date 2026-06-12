import { endpoints } from "@/lib/api/endpoints";
import { request } from "@/lib/api/client";
import type {
  GovernanceMaturityResponse,
  HealthExplanationsResponse,
  ExecutivePriorityItem,
  RootCauseAnalyticsResponse,
  StrategicRecommendationsResponse,
  GovernanceTrendsResponse,
  ExecutiveBriefingResponse,
  CopilotResponse
} from "@/types/api";

export function getGovernanceMaturity(): Promise<GovernanceMaturityResponse> {
  return request<GovernanceMaturityResponse>({
    method: "GET",
    url: endpoints.maturity,
  });
}

export function getHealthExplanations(): Promise<HealthExplanationsResponse> {
  return request<HealthExplanationsResponse>({
    method: "GET",
    url: endpoints.healthExplanations,
  });
}

export function getExecutivePriorities(): Promise<ExecutivePriorityItem[]> {
  return request<ExecutivePriorityItem[]>({
    method: "GET",
    url: endpoints.executivePriorities,
  });
}

export function getRootCauseAnalytics(): Promise<RootCauseAnalyticsResponse> {
  return request<RootCauseAnalyticsResponse>({
    method: "GET",
    url: endpoints.rootCauseAnalytics,
  });
}

export function getPortfolioRecommendations(): Promise<StrategicRecommendationsResponse> {
  return request<StrategicRecommendationsResponse>({
    method: "GET",
    url: endpoints.portfolioRecommendations,
  });
}

export function getGovernanceTrends(): Promise<GovernanceTrendsResponse> {
  return request<GovernanceTrendsResponse>({
    method: "GET",
    url: endpoints.trends,
  });
}

export function getExecutiveBriefing(): Promise<ExecutiveBriefingResponse> {
  return request<ExecutiveBriefingResponse>({
    method: "GET",
    url: endpoints.executiveBriefing,
  });
}

export function askGovernanceCopilot(query: string): Promise<CopilotResponse> {
  return request<CopilotResponse>({
    method: "POST",
    url: endpoints.copilot,
    data: { query },
  });
}

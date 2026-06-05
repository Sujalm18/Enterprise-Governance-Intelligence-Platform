export const endpoints = {
  root: "/",
  health: "/health",
  upload: "/api/upload",
  workflowJob: (id: number | string) => `/api/workflow/jobs/${id}`,
  reports: "/api/governance/reports",
  report: (id: number | string) => `/api/governance/reports/${id}`,
  reviewReport: (id: number | string) => `/api/governance/reports/${id}/review`,
  dashboardStats: "/api/governance/dashboard/stats",
  dashboardCharts: "/api/governance/dashboard/charts",
  escalations: "/api/governance/escalations",
  routeEscalation: (id: number | string) => `/api/governance/escalations/${id}/route`,
} as const;

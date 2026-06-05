import type { ListEscalationsParams, ListReportsParams } from "@/types/api";

export const queryKeys = {
  health: ["health"] as const,
  dashboard: {
    stats: ["dashboard", "stats"] as const,
    charts: ["dashboard", "charts"] as const,
  },
  workflow: {
    job: (id: number | string) => ["workflow", "job", String(id)] as const,
  },
  reports: {
    list: (params?: ListReportsParams) => ["reports", "list", params ?? {}] as const,
    detail: (id: number | string) => ["reports", "detail", String(id)] as const,
    pendingReview: ["reports", "pending-review"] as const,
  },
  escalations: {
    list: (params?: ListEscalationsParams) =>
      ["escalations", "list", params ?? {}] as const,
  },
} as const;

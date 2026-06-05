export type WorkflowStatus =
  | "uploaded"
  | "processing"
  | "pending_review"
  | "approved"
  | "published"
  | "failed";

export type ReviewStatus = "pending_review" | "approved" | "changes_requested";

export type RaidItemType = "risk" | "action" | "issue" | "dependency" | string;

export type Severity = "low" | "medium" | "high" | "critical" | string;

export type EscalationStatus = "open" | "routed" | "resolved" | string;

export type GovernanceRelevance = "low" | "medium" | "high";

export type DocumentResponse = {
  id: number;
  filename: string;
  type: string;
  upload_timestamp: string;
  status: WorkflowStatus;
};

export type WorkflowJobResponse = {
  id: number;
  document_id: number;
  status: WorkflowStatus;
  logs: string;
  updated_at: string;
};

export type RaidItemResponse = {
  id: number;
  report_id: number;
  type: RaidItemType;
  description: string;
  severity: Severity;
  confidence_score: number;
  source_excerpt: string | null;
};

export type EscalationItemResponse = {
  id: number;
  report_id: number;
  filename: string;
  description: string;
  severity: Severity;
  source_excerpt: string | null;
  confidence_score: number;
  status: EscalationStatus;
  routing_target: string | null;
  created_at: string;
};

export type MeetingActionResponse = {
  id?: number;
  report_id?: number;
  owner: string;
  task: string;
  due_date: string | null;
  created_at?: string;
};

export type GovernanceReportResponse = {
  id: number;
  document_id: number;
  filename: string;
  summary: string;
  executive_summary: string;
  confidence_score: number;
  model_version: string;
  prompt_version: string;
  review_status: ReviewStatus | string;
  reviewer: string | null;
  review_notes: string | null;
  processing_time_seconds: number;
  tokens_used: number;
  provider_name: string;
  version: number;
  is_latest: boolean;
  created_at: string;
  updated_at: string;
  raid_items: RaidItemResponse[];
  escalation_items: EscalationItemResponse[];
  meeting_actions?: MeetingActionResponse[];
  document_type?: string | null;
  classification_confidence?: number | null;
  governance_relevance?: GovernanceRelevance | string | null;
};

export type AuditLogResponse = {
  id: number;
  document_id: number | null;
  governance_report_id: number | null;
  event: string;
  user: string;
  details: string | null;
  timestamp: string;
};

export type DashboardStatsResponse = {
  total_documents: number;
  pending_reviews: number;
  approved_reports: number;
  failed_jobs: number;
  total_escalations: number;
  open_escalations: number;
  average_confidence: number;
  average_processing_time: number;
  total_tokens_consumed: number;
  reports_generated: number;
  recent_logs: AuditLogResponse[];
};

export type StatusCount = {
  label: string;
  count: number;
};

export type TrendPoint = {
  date: string;
  count: number;
};

export type DashboardChartsResponse = {
  reports_by_status: StatusCount[];
  escalations_by_severity: StatusCount[];
  raid_distribution: StatusCount[];
  processing_trend: TrendPoint[];
};

export type ReportReviewRequest = {
  reviewer: string;
  review_status: "approved" | "changes_requested";
  review_notes?: string | null;
};

export type EscalationRouteRequest = {
  routing_target: string;
};

export type ListReportsParams = {
  is_latest?: boolean;
  review_status?: ReviewStatus | string;
};

export type ListEscalationsParams = {
  status?: EscalationStatus;
};

export type UploadDocumentParams = {
  chunk_size?: number;
  chunk_overlap?: number;
  use_rag?: boolean;
};

export type HealthResponse = {
  status: string;
  service: string;
  provider: string;
  mock_mode_active: boolean;
};

export type ApiErrorPayload = {
  detail?: string;
  message?: string;
  [key: string]: unknown;
};

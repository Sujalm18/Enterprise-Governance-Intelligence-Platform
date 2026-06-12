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
  
  // Phase 2 Decision Support reserved columns
  recommended_mitigations?: string[] | null;
  implementation_effort?: string | null;
  expected_risk_reduction?: string | null;
  recommended_priority?: string | null;
  suggested_owner_role?: string | null;
  priority?: string | null;
  risk_score?: number;
  current_risk_score?: number;
  explainability_trace?: Record<string, any> | null;

  // Phase 5 AI Insights columns
  explain_why?: string | null;
  suggested_actions?: string | null;
  estimated_impact?: string | null;
  tenant_id?: number | null;
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
  
  // Ownership
  raised_by?: string | null;
  assigned_to?: string | null;
  resolved_by?: string | null;

  // Phase 2 Decision Support columns
  remediation_plan?: string | null;
  expected_risk_reduction?: string | null;
  priority?: string | null;
  suggested_owner_role?: string | null;
  risk_score?: number;
  explainability_trace?: Record<string, any> | null;

  // Phase 5 AI Insights columns
  explain_why?: string | null;
  suggested_actions?: string | null;
  estimated_impact?: string | null;
  tenant_id?: number | null;
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
  
  // Workflow
  created_by?: string | null;
  assigned_to?: string | null;
  approved_by?: string | null;
  status?: string | null;
};

export type AuditLogResponse = {
  id: number;
  document_id: number | null;
  governance_report_id: number | null;
  event: string;
  user: string;
  details: string | null;
  timestamp: string;
  
  // Unified AuditEvent timeline properties
  user_role: string;
  action: string;
  entity_type?: string | null;
  entity_id?: number | null;
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
  
  // Phase 3 Mitigation KPIs
  governance_health_score: number;
  total_original_risk: number;
  total_current_risk: number;
  risk_reduction_percentage: number;
  overdue_mitigations_count: number;
  mitigations_pipeline_counts: Record<string, number>;

  // Phase 4 & 4.5 KPIs
  unread_notifications: number;
  sla_breaches_count: number;
  pending_governance_approvals: number;
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

export type MitigationTaskResponse = {
  id: number;
  title: string;
  description: string | null;
  related_raid_item_id: number;
  related_escalation_id: number | null;
  owner_role: string;
  owner_name: string | null;
  priority: string;
  risk_score: number;
  target_date: string | null;
  sla_status: "ON_TRACK" | "AT_RISK" | "OVERDUE" | string;
  status: "PLANNED" | "IN_PROGRESS" | "BLOCKED" | "COMPLETED" | "VERIFIED" | string;
  completion_percentage: number;
  effectiveness: number;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  verified_at: string | null;
  explainability_trace?: Record<string, any> | null;
};

export type MitigationTaskUpdateRequest = {
  title?: string;
  description?: string | null;
  owner_role?: string;
  owner_name?: string | null;
  priority?: string;
  target_date?: string | null;
  status?: string;
  completion_percentage?: number;
  effectiveness?: number;
};

export type NotificationResponse = {
  id: number;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL" | string;
  notification_type: string;
  title: string;
  message: string;
  recipient_role: string;
  related_entity_type: "report" | "escalation" | "mitigation" | "document" | string | null;
  related_entity_id: number | null;
  read_status: boolean;
  created_at: string;
};

export type InboxResponse = {
  pending_reviews: GovernanceReportResponse[];
  assigned_escalations: EscalationItemResponse[];
  assigned_mitigations: MitigationTaskResponse[];
  pending_verifications: MitigationTaskResponse[];
};

export type OrganizationResponse = {
  id: number;
  name: string;
  created_at: string;
};


// Phase 6 GRC Intelligence
export interface GovernanceMaturityDimensions {
  policy_ownership: number;
  mitigation_completion: number;
  sla_compliance: number;
  escalation_closure: number;
  risk_reduction: number;
}

export interface GovernanceBenchmark {
  industry_average: number;
  peer_percentile: number;
}

export interface GovernanceMaturityResponse {
  score: number;
  tier: string;
  dimensions: GovernanceMaturityDimensions;
  benchmark: GovernanceBenchmark;
  appetite_alignment: string;
}

export interface HealthExplanationItem {
  description: string;
  impact: number;
}

export interface HealthExplanationsResponse {
  health_score: number;
  main_drivers: HealthExplanationItem[];
  positive_contributions: HealthExplanationItem[];
}

export interface ExecutivePriorityItem {
  title: string;
  severity: string;
  count: number;
  impact: string;
  priority_score: number;
  reason: string;
}

export interface RootCauseAnalyticsResponse {
  category_distribution: Record<string, number>;
  category_risk_scores: Record<string, number>;
  failure_patterns: string[];
}

export interface StrategicRecommendationsResponse {
  quick_wins: string[];
  medium_term: string[];
  strategic: string[];
}

export interface ExecutiveBriefingResponse {
  executive_summary: string;
  current_state: string;
  key_risks: string;
  operational_concerns: string;
  recommendations: string;
  next_30_days: string;
  full_markdown: string;
}

export interface CopilotRequest {
  query: string;
}

export interface CopilotResponse {
  response: string;
}

export interface GovernanceTrendPoint {
  date: string;
  health_score: number;
  maturity_score: number;
  risk_exposure: number;
  mitigation_effectiveness_pct: number;
  sla_breaches: number;
  open_escalations: number;
  verified_mitigations: number;
  critical_risks: number;
  notification_volume: number;
}

export interface GovernanceTrendsResponse {
  trend_points: GovernanceTrendPoint[];
}




import os
import re
from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from backend.app.models import WorkflowStatus

# Document Classification Constants
DOCUMENT_TYPES = [
    "meeting_minutes",
    "project_status_report",
    "raid_register",
    "governance_report",
    "steering_committee_pack",
    "executive_report",
    "generic_business_document",
    "escalation_memo",
    "noisy_ocr_document",
    "edge_case_document"
]

GOVERNANCE_RELEVANCE_LEVELS = ["low", "medium", "high"]

# Governance Scoring Constants
POSITIVE_GOVERNANCE_INDICATORS = {
    "raid": 30,
    "risk register": 30,
    "escalation": 30,
    "escalated": 30,
    "dependency": 15,
    "mitigation": 15,
    "owner": 5,
    "target date": 5,
    "rag": 20,
    "steering committee": 25,
    "executive review": 20,
    "severity": 10
}

WEAK_GOVERNANCE_INDICATORS = {
    "action item": -10,
    "meeting minutes": -10,
    "agenda": -5,
    "discussion": -5,
    "minutes": -5
}

ESCALATION_TERMS = [
    "escalation",
    "escalated",
    "steering committee",
    "executive review",
    "board review",
    "requires executive decision",
    "requires approval",
    "management intervention"
]

GOVERNANCE_KEYWORDS = [
    "raid",
    "risk",
    "issue",
    "dependency",
    "escalation",
    "mitigation",
    "rag",
    "severity",
    "owner",
    "target date"
]

# Generic Config for ORM mappings
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# User Schemas
class UserResponse(BaseSchema):
    id: int
    username: str
    role: str

# Document Schemas
class DocumentResponse(BaseSchema):
    id: int
    filename: str
    type: str
    upload_timestamp: datetime
    status: WorkflowStatus

    @field_validator("filename", mode="before")
    @classmethod
    def clean_filename(cls, v):
        if not v:
            return ""
        base = os.path.basename(v)
        return re.sub(r'^\d+_', '', base)

# Workflow Job Schemas
class WorkflowJobResponse(BaseSchema):
    id: int
    document_id: int
    status: WorkflowStatus
    logs: str
    updated_at: datetime

# AI Structural Extractions Schemas
class RaidItemSchema(BaseModel):
    type: str = Field(..., description="Must be one of: risk, action, issue, dependency")
    description: str = Field(..., description="Details of the risk, action, issue, or dependency")
    severity: str = Field(..., description="Must be one of: low, medium, high, critical")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    source_excerpt: Optional[str] = Field(default=None, description="Verbatim text sentence or clause from source")
    
    # Phase 2 Decision Support reserved columns
    recommended_mitigations: Optional[List[str]] = Field(default=None, description="Actionable recommendations if item is a risk")
    implementation_effort: Optional[str] = Field(default=None, description="Low, Medium, or High if item is a risk")
    expected_risk_reduction: Optional[str] = Field(default=None, description="Low, Medium, or High if item is a risk")
    recommended_priority: Optional[str] = Field(default=None, description="P1, P2, P3, or P4 if item is a risk")
    suggested_owner_role: Optional[str] = Field(default=None, description="Analyst, Manager, or Governance Lead if item is a risk")
    priority: Optional[str] = Field(default=None, description="P1, P2, P3, or P4")
    risk_score: int = Field(default=0, description="Original Risk Score from 0 to 100")
    current_risk_score: int = Field(default=0, description="Current Residual Risk Score from 0 to 100")
    explainability_trace: Optional[dict] = Field(default=None, description="Structured explainability trace")
    
    # Priority 1 & 5 Additions
    explain_why: Optional[str] = Field(default=None, description="Context-specific explanation of why this risk/issue matters")
    suggested_actions: Optional[str] = Field(default=None, description="Context-specific recommended action steps")
    estimated_impact: Optional[str] = Field(default=None, description="Estimated percentage/text risk reduction statement")
    tenant_id: Optional[int] = Field(default=1, description="Tenant ID identifier")

    @field_validator("recommended_mitigations", mode="before")
    @classmethod
    def decode_mitigations(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [x.strip() for x in v.split(",") if x.strip()]
        return v

    @field_validator("explainability_trace", mode="before")
    @classmethod
    def decode_explainability(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return {"playbook": None, "matched_keywords": [], "recommendation_source": "error_parsing", "evidence": [v]}
        return v

class EscalationItemSchema(BaseModel):
    description: str = Field(..., description="Actionable escalation summary")
    severity: str = Field(..., description="Must be one of: low, medium, high, critical")
    source_excerpt: Optional[str] = Field(default=None, description="Verbatim text sentence or clause from source")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Phase 2 Decision Support columns
    remediation_plan: Optional[str] = Field(default=None, description="Recommended remediation plan for the escalation")
    expected_risk_reduction: Optional[str] = Field(default=None, description="Expected risk reduction: Low, Medium, or High")
    priority: Optional[str] = Field(default=None, description="Priority: P1, P2, P3, or P4")
    suggested_owner_role: Optional[str] = Field(default=None, description="Suggested owner role: Analyst, Manager, or Governance Lead")
    risk_score: int = Field(default=0, description="Risk Score from 0 to 100")
    explainability_trace: Optional[dict] = Field(default=None, description="Structured explainability trace")
    
    # Priority 1 & 5 Additions
    explain_why: Optional[str] = Field(default=None, description="Context-specific explanation of why this escalation matters")
    suggested_actions: Optional[str] = Field(default=None, description="Context-specific recommended action steps")
    estimated_impact: Optional[str] = Field(default=None, description="Estimated percentage/text risk reduction statement")
    tenant_id: Optional[int] = Field(default=1, description="Tenant ID identifier")

    @field_validator("explainability_trace", mode="before")
    @classmethod
    def decode_explainability(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return {"playbook": None, "matched_keywords": [], "recommendation_source": "error_parsing", "evidence": [v]}
        return v

class MeetingActionSchema(BaseModel):
    owner: str = Field(..., description="Person assigned to the action")
    task: str = Field(..., description="Description of the action item")
    due_date: Optional[str] = Field(default=None, description="Due date for the action if specified")

class AIReportExtractionSchema(BaseModel):
    summary: str = Field(..., description="Detailed governance summary of status")
    executive_summary: str = Field(..., description="High-level narrative for executives")
    raid_items: List[RaidItemSchema] = Field(default_factory=list)
    escalation_items: List[EscalationItemSchema] = Field(default_factory=list)
    meeting_actions: List[MeetingActionSchema] = Field(default_factory=list)
    document_type: str = Field(default="generic_business_document", description="Type of document classified")
    classification_confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence in document classification")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    tokens_used: Optional[int] = 0
    governance_relevance: str = Field(default="medium", description="Governance content relevance: low, medium, or high")
    governance_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    raid_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    escalation_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    meeting_action_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    ocr_confidence: float = Field(default=1.0, ge=0.0, le=1.0)

# Database Persistence Response Schemas
class RaidItemResponse(BaseSchema, RaidItemSchema):
    id: int
    report_id: int

class EscalationItemResponse(BaseSchema, EscalationItemSchema):
    id: int
    report_id: int
    filename: str
    status: str
    routing_target: Optional[str] = None
    created_at: datetime
    
    # Ownership
    raised_by: Optional[str] = None
    assigned_to: Optional[str] = None
    resolved_by: Optional[str] = None

class GovernanceReportResponse(BaseSchema):
    id: int
    document_id: int
    filename: str
    summary: str
    executive_summary: str
    confidence_score: float
    model_version: str
    prompt_version: str
    review_status: str
    reviewer: Optional[str] = None
    review_notes: Optional[str] = None
    processing_time_seconds: float
    tokens_used: int
    provider_name: str
    version: int
    is_latest: bool
    created_at: datetime
    updated_at: datetime
    raid_items: List[RaidItemResponse]
    escalation_items: List[EscalationItemResponse]
    
    # Workflow
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None
    approved_by: Optional[str] = None
    status: str

# Request Schemas
class ReportAssignRequest(BaseModel):
    assigned_to: str

class EscalationAssignRequest(BaseModel):
    assigned_to: str

class ReportReviewRequest(BaseModel):
    reviewer: str = Field(..., min_length=1)
    review_status: str = Field(..., pattern="^(approved|changes_requested)$")
    review_notes: Optional[str] = None

class EscalationRouteRequest(BaseModel):
    routing_target: str = Field(..., min_length=1)

# Audit Log Response
class AuditLogResponse(BaseSchema):
    id: int
    document_id: Optional[int] = None
    governance_report_id: Optional[int] = None
    event: str
    user: str
    details: Optional[str] = None
    timestamp: datetime
    
    # Unified AuditEvent timeline properties
    user_role: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None

class MitigationTaskSchema(BaseModel):
    title: str = Field(..., description="Actionable title for the mitigation task")
    description: Optional[str] = Field(default=None, description="Detailed description")
    related_raid_item_id: int = Field(..., description="Foreign key to RaidItem")
    related_escalation_id: Optional[int] = Field(default=None, description="Foreign key to EscalationItem")
    owner_role: str = Field(..., description="Analyst, Manager, or Governance Lead")
    owner_name: Optional[str] = Field(default=None, description="Assigned individual name")
    priority: str = Field(..., description="P1, P2, P3, or P4")
    risk_score: int = Field(..., description="Originating risk score")
    target_date: Optional[str] = Field(default=None, description="Target due date in YYYY-MM-DD format")
    sla_status: str = Field(default="ON_TRACK", description="ON_TRACK, AT_RISK, or OVERDUE")
    status: str = Field(default="PLANNED", description="PLANNED, IN_PROGRESS, BLOCKED, COMPLETED, or VERIFIED")
    completion_percentage: int = Field(default=0, ge=0, le=100)
    effectiveness: int = Field(default=20, ge=0, le=100)


class MitigationTaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    owner_role: Optional[str] = None
    owner_name: Optional[str] = None
    priority: Optional[str] = None
    target_date: Optional[str] = None
    status: Optional[str] = None
    completion_percentage: Optional[int] = None
    effectiveness: Optional[int] = None

class MitigationTaskResponse(BaseSchema, MitigationTaskSchema):
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    explainability_trace: Optional[dict] = None

    @field_validator("explainability_trace", mode="before")
    @classmethod
    def decode_explainability(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return {"playbook": None, "matched_keywords": [], "recommendation_source": "error_parsing", "evidence": [v]}
        return v

# Stats for Dashboard
class DashboardStatsResponse(BaseModel):
    total_documents: int
    pending_reviews: int
    approved_reports: int
    failed_jobs: int
    total_escalations: int
    open_escalations: int
    average_confidence: float
    average_processing_time: float
    total_tokens_consumed: int
    reports_generated: int
    recent_logs: List[AuditLogResponse]
    
    # Phase 3 Mitigation KPIs
    governance_health_score: int = 100
    total_original_risk: int = 0
    total_current_risk: int = 0
    risk_reduction_percentage: float = 0.0
    overdue_mitigations_count: int = 0
    mitigations_pipeline_counts: dict = Field(default_factory=dict)

    # Phase 4 & 4.5 KPIs
    unread_notifications: int = 0
    sla_breaches_count: int = 0
    pending_governance_approvals: int = 0


# Chart data for Executive Dashboard
class StatusCount(BaseModel):
    label: str
    count: int

class TrendPoint(BaseModel):
    date: str
    count: int

class DashboardChartsResponse(BaseModel):
    reports_by_status: List[StatusCount]
    escalations_by_severity: List[StatusCount]
    raid_distribution: List[StatusCount]
    processing_trend: List[TrendPoint]


class NotificationResponse(BaseSchema):
    id: int
    severity: str
    notification_type: str
    title: str
    message: str
    recipient_role: str
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    read_status: bool
    created_at: datetime


class NotificationReadRequest(BaseModel):
    read_status: bool = True


class DemoDataGenerateRequest(BaseModel):
    size: Literal["small", "medium", "enterprise"]


class InboxResponse(BaseModel):
    pending_reviews: List[GovernanceReportResponse]
    assigned_escalations: List[EscalationItemResponse]
    assigned_mitigations: List[MitigationTaskResponse]
    pending_verifications: List[MitigationTaskResponse]


# Phase 6 Governance Intelligence Schemas
class GovernanceMaturityDimensions(BaseModel):
    policy_ownership: int
    mitigation_completion: int
    sla_compliance: int
    escalation_closure: int
    risk_reduction: int

class GovernanceBenchmark(BaseModel):
    industry_average: int
    peer_percentile: int

class GovernanceMaturityResponse(BaseModel):
    score: int
    tier: str
    dimensions: GovernanceMaturityDimensions
    benchmark: GovernanceBenchmark
    appetite_alignment: str

class ExecutivePriorityItem(BaseModel):
    title: str
    severity: str
    count: int
    impact: str
    priority_score: int
    reason: str

class RootCauseAnalyticsResponse(BaseModel):
    category_distribution: dict
    category_risk_scores: dict
    failure_patterns: List[str]

class StrategicRecommendationsResponse(BaseModel):
    quick_wins: List[str]
    medium_term: List[str]
    strategic: List[str]

class ExecutiveBriefingResponse(BaseModel):
    executive_summary: str
    current_state: str
    key_risks: str
    operational_concerns: str
    recommendations: str
    next_30_days: str
    full_markdown: str

class CopilotRequest(BaseModel):
    query: str

class CopilotResponse(BaseModel):
    response: str

class GovernanceTrendPoint(BaseModel):
    date: str
    health_score: int
    maturity_score: int
    risk_exposure: int
    mitigation_effectiveness_pct: float
    sla_breaches: int
    open_escalations: int
    verified_mitigations: int
    critical_risks: int
    notification_volume: int

class GovernanceTrendsResponse(BaseModel):
    trend_points: List[GovernanceTrendPoint]


class HealthExplanationItem(BaseModel):
    description: str
    impact: int

class HealthExplanationsResponse(BaseModel):
    health_score: int
    main_drivers: List[HealthExplanationItem]
    positive_contributions: List[HealthExplanationItem]



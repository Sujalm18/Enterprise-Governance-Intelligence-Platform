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

class EscalationItemSchema(BaseModel):
    description: str = Field(..., description="Actionable escalation summary")
    severity: str = Field(..., description="Must be one of: low, medium, high, critical")
    source_excerpt: Optional[str] = Field(default=None, description="Verbatim text sentence or clause from source")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)

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

# Request Schemas
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

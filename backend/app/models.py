import enum
import os
import re
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from backend.app.database import Base

class WorkflowStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    FAILED = "failed"

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    slack_webhook_url = Column(String, nullable=True)
    teams_webhook_url = Column(String, nullable=True)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # "analyst" or "reviewer"
    tenant_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), default=1, nullable=True)

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "pdf", "docx", "txt"
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.UPLOADED, nullable=False)
    tenant_id = Column(Integer, default=1, nullable=True)
    
    workflow_jobs = relationship("WorkflowJob", back_populates="document", cascade="all, delete-orphan")
    reports = relationship("GovernanceReport", back_populates="document", cascade="all, delete-orphan")

class WorkflowJob(Base):
    __tablename__ = "workflow_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.UPLOADED, nullable=False)
    logs = Column(Text, default="", nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    tenant_id = Column(Integer, default=1, nullable=True)
    
    document = relationship("Document", back_populates="workflow_jobs")

class GovernanceReport(Base):
    __tablename__ = "governance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=False)
    executive_summary = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)
    model_version = Column(String, default="unknown", nullable=False)
    prompt_version = Column(String, default="v1", nullable=False)
    
    # Document classification
    document_type = Column(String, nullable=True)
    classification_confidence = Column(Float, nullable=True)
    governance_relevance = Column(String, nullable=True)
    
    # Review columns
    review_status = Column(String, default="pending_review", nullable=False)  # "pending_review", "approved", "changes_requested"
    reviewer = Column(String, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Workflow Phase 1 columns
    created_by = Column(String, default="Analyst", nullable=True)
    assigned_to = Column(String, default="Manager", nullable=True)
    approved_by = Column(String, nullable=True)
    status = Column(String, default="PENDING_MANAGER_REVIEW", nullable=False)
    
    # Processing metrics
    processing_time_seconds = Column(Float, default=0.0, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    provider_name = Column(String, default="unknown", nullable=False)
    
    # Report versioning
    version = Column(Integer, default=1, nullable=False)
    is_latest = Column(Boolean, default=True, nullable=False)
    tenant_id = Column(Integer, default=1, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    document = relationship("Document", back_populates="reports")
    raid_items = relationship("RaidItem", back_populates="report", cascade="all, delete-orphan")
    escalation_items = relationship("EscalationItem", back_populates="report", cascade="all, delete-orphan")
    meeting_actions = relationship("MeetingAction", back_populates="report", cascade="all, delete-orphan")

    @property
    def filename(self) -> str:
        if self.document:
            base = os.path.basename(self.document.filename)
            return re.sub(r'^\d+_', '', base)
        return ""

class RaidItem(Base):
    __tablename__ = "raid_items"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("governance_reports.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)  # "risk", "action", "issue", "dependency"
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # "low", "medium", "high", "critical"
    confidence_score = Column(Float, default=1.0, nullable=False)
    source_excerpt = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Reserved columns for Phase 2 Decision Support
    recommended_mitigations = Column(Text, nullable=True) # JSON list
    implementation_effort = Column(String, nullable=True)
    expected_risk_reduction = Column(String, nullable=True)
    recommended_priority = Column(String, nullable=True)
    suggested_owner_role = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    risk_score = Column(Integer, default=0, nullable=False)
    current_risk_score = Column(Integer, default=0, nullable=False)
    explainability_trace = Column(Text, nullable=True)
    
    # Priority 1 & 5 Additions
    explain_why = Column(Text, nullable=True)
    suggested_actions = Column(Text, nullable=True)
    estimated_impact = Column(Text, nullable=True)
    tenant_id = Column(Integer, default=1, nullable=True)
    
    report = relationship("GovernanceReport", back_populates="raid_items")

class EscalationItem(Base):
    __tablename__ = "escalation_items"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("governance_reports.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # "low", "medium", "high", "critical"
    status = Column(String, default="OPEN", nullable=False)  # "OPEN", "ASSIGNED", "UNDER_REVIEW", "RESOLVED", "CLOSED"
    routing_target = Column(String, nullable=True)
    source_excerpt = Column(Text, nullable=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Ownership columns
    raised_by = Column(String, nullable=True)
    assigned_to = Column(String, nullable=True)
    resolved_by = Column(String, nullable=True)
    
    # Phase 2 Decision Support columns
    remediation_plan = Column(Text, nullable=True)
    expected_risk_reduction = Column(String, nullable=True)
    priority = Column(String, nullable=True)
    suggested_owner_role = Column(String, nullable=True)
    risk_score = Column(Integer, default=0, nullable=False)
    explainability_trace = Column(Text, nullable=True)
    
    # Priority 1 & 5 Additions
    explain_why = Column(Text, nullable=True)
    suggested_actions = Column(Text, nullable=True)
    estimated_impact = Column(Text, nullable=True)
    tenant_id = Column(Integer, default=1, nullable=True)
    
    report = relationship("GovernanceReport", back_populates="escalation_items")

    @property
    def filename(self) -> str:
        if self.report and self.report.document:
            base = os.path.basename(self.report.document.filename)
            return re.sub(r'^\d+_', '', base)
        return ""

class MeetingAction(Base):
    __tablename__ = "meeting_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("governance_reports.id", ondelete="CASCADE"), nullable=False)
    owner = Column(String, nullable=False)
    task = Column(Text, nullable=False)
    due_date = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    tenant_id = Column(Integer, default=1, nullable=True)
    
    report = relationship("GovernanceReport", back_populates="meeting_actions")

class MitigationTask(Base):
    __tablename__ = "mitigation_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    related_raid_item_id = Column(Integer, ForeignKey("raid_items.id", ondelete="CASCADE"), nullable=False)
    related_escalation_id = Column(Integer, ForeignKey("escalation_items.id", ondelete="SET NULL"), nullable=True)
    owner_role = Column(String, nullable=False)  # Analyst | Manager | Governance Lead
    owner_name = Column(String, nullable=True)
    priority = Column(String, nullable=False)    # P1 | P2 | P3 | P4
    risk_score = Column(Integer, nullable=False)
    target_date = Column(String, nullable=True)     # YYYY-MM-DD
    sla_status = Column(String, default="ON_TRACK", nullable=False) # ON_TRACK | AT_RISK | OVERDUE
    status = Column(String, default="PLANNED", nullable=False) # PLANNED | IN_PROGRESS | BLOCKED | COMPLETED | VERIFIED
    completion_percentage = Column(Integer, default=0, nullable=False)
    effectiveness = Column(Integer, default=20, nullable=False) # default 20%
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    tenant_id = Column(Integer, default=1, nullable=True)
    
    raid_item = relationship("RaidItem")
    escalation = relationship("EscalationItem")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=True)
    governance_report_id = Column(Integer, nullable=True)
    event = Column(String, nullable=False)  # e.g., "Uploaded", "Processed", "Approved", "Changes Requested"
    user = Column(String, nullable=False)   # e.g., "analyst_user", "reviewer_user", "system"
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Extended fields to fulfill AuditEvent workflow logging
    user_role = Column(String, default="Analyst", nullable=False)
    action = Column(String, default="event", nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    tenant_id = Column(Integer, default=1, nullable=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(String, nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    notification_type = Column(String, nullable=False)  # e.g., REPORT_PENDING_REVIEW, SLA_BREACH
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    recipient_role = Column(String, nullable=False)  # Analyst | Manager | Governance Lead
    related_entity_type = Column(String, nullable=True)  # report | escalation | mitigation | document
    related_entity_id = Column(Integer, nullable=True)
    read_status = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    tenant_id = Column(Integer, default=1, nullable=True)


class GovernanceTrendSnapshot(Base):
    __tablename__ = "governance_trend_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    health_score = Column(Integer, nullable=False)
    maturity_score = Column(Integer, nullable=False)
    risk_exposure = Column(Integer, nullable=False)
    mitigation_effectiveness_pct = Column(Float, nullable=False)
    sla_breaches = Column(Integer, nullable=False)
    open_escalations = Column(Integer, nullable=False)
    verified_mitigations = Column(Integer, nullable=False)
    critical_risks = Column(Integer, nullable=False)
    notification_volume = Column(Integer, nullable=False)
    tenant_id = Column(Integer, default=1, nullable=True)



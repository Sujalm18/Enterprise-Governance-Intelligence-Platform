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

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, nullable=False)  # "analyst" or "reviewer"

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "pdf", "docx", "txt"
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.UPLOADED, nullable=False)
    
    workflow_jobs = relationship("WorkflowJob", back_populates="document", cascade="all, delete-orphan")
    reports = relationship("GovernanceReport", back_populates="document", cascade="all, delete-orphan")

class WorkflowJob(Base):
    __tablename__ = "workflow_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.UPLOADED, nullable=False)
    logs = Column(Text, default="", nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
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
    
    # Processing metrics
    processing_time_seconds = Column(Float, default=0.0, nullable=False)
    tokens_used = Column(Integer, default=0, nullable=False)
    provider_name = Column(String, default="unknown", nullable=False)
    
    # Report versioning
    version = Column(Integer, default=1, nullable=False)
    is_latest = Column(Boolean, default=True, nullable=False)
    
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
    
    report = relationship("GovernanceReport", back_populates="raid_items")

class EscalationItem(Base):
    __tablename__ = "escalation_items"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("governance_reports.id", ondelete="CASCADE"), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String, nullable=False)  # "low", "medium", "high", "critical"
    status = Column(String, default="open", nullable=False)  # "open", "routed", "resolved"
    routing_target = Column(String, nullable=True)
    source_excerpt = Column(Text, nullable=True)
    confidence_score = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
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
    
    report = relationship("GovernanceReport", back_populates="meeting_actions")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, nullable=True)
    governance_report_id = Column(Integer, nullable=True)
    event = Column(String, nullable=False)  # e.g., "Uploaded", "Processed", "Approved", "Changes Requested"
    user = Column(String, nullable=False)   # e.g., "analyst_user", "reviewer_user", "system"
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

import logging
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from sqlalchemy.exc import OperationalError

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.migrations import is_schema_mismatch_error, schema_mismatch_response_detail
from backend.app.models import (
    Document, WorkflowJob, WorkflowStatus, GovernanceReport, RaidItem, EscalationItem, AuditLog, User
)
from backend.app.schemas import (
    DocumentResponse, WorkflowJobResponse, GovernanceReportResponse,
    ReportReviewRequest, EscalationRouteRequest, DashboardStatsResponse,
    EscalationItemResponse, AuditLogResponse, DashboardChartsResponse
)
from backend.app.services.workflow import process_document_pipeline

logger = logging.getLogger("governance_copilot.api.endpoints")
router = APIRouter()


def _raise_schema_mismatch_http_error(error: OperationalError) -> None:
    logger.error("Database schema mismatch detected while querying reports: %s", error)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=schema_mismatch_response_detail(error)
    )

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    chunk_size: Optional[int] = Query(None),
    chunk_overlap: Optional[int] = Query(None),
    use_rag: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Uploads a document, creates a DB entry and WorkflowJob,
    and runs the background worker pipeline.
    """
    logger.info(f"Incoming upload request for file: {file.filename}")
    
    # Validate extension
    file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in ("pdf", "docx", "txt", "doc"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{file_ext}'. Supported formats: PDF, DOCX, TXT"
        )
        
    # Override settings if provided in request
    if chunk_size is not None:
        settings.CHUNK_SIZE = chunk_size
    if chunk_overlap is not None:
        settings.CHUNK_OVERLAP = chunk_overlap
    if use_rag is not None:
        settings.USE_RAG = use_rag

    # Save file to uploads folder
    filename_clean = f"{int(time.time())}_{file.filename}"
    file_path = Path(settings.UPLOAD_DIR) / filename_clean
    
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        logger.error(f"Failed to write file to disk: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save file to disk."
        )

    # 1. Create Document Record
    doc = Document(
        filename=str(file_path),
        type=file_ext,
        status=WorkflowStatus.UPLOADED
    )
    db.add(doc)
    db.commit()
    
    # 2. Create WorkflowJob Record
    job = WorkflowJob(
        document_id=doc.id,
        status=WorkflowStatus.UPLOADED,
        logs=f"File uploaded. Saved to: {file_path.name}\n"
    )
    db.add(job)
    db.commit()
    
    # 3. Log Audit Trail
    audit = AuditLog(
        document_id=doc.id,
        event="Uploaded",
        user="analyst_user",  # Defaulting to analyst role
        details=f"Document '{file.filename}' uploaded and queued for processing."
    )
    db.add(audit)
    db.commit()

    # 4. Dispatch background worker pipeline task
    background_tasks.add_task(
        process_document_pipeline,
        document_id=doc.id,
        job_id=job.id
    )

    logger.info(f"Background task queued. Job ID: {job.id}, Document ID: {doc.id}")
    return doc

@router.get("/workflow/jobs/{id}", response_model=WorkflowJobResponse)
def get_workflow_job(id: int, db: Session = Depends(get_db)):
    """Retrieves status and logs of a workflow job."""
    job = db.query(WorkflowJob).filter(WorkflowJob.id == id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow job not found")
    return job

@router.get("/governance/reports", response_model=List[GovernanceReportResponse])
def list_governance_reports(
    is_latest: bool = Query(True),
    review_status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists governance reports, default returns latest version only."""
    # Eager-load Document relationship to avoid N+1 queries and include filename
    query = db.query(GovernanceReport).options(joinedload(GovernanceReport.document))
    if is_latest:
        query = query.filter(GovernanceReport.is_latest == True)
    if review_status:
        query = query.filter(GovernanceReport.review_status == review_status)

    try:
        reports = query.order_by(GovernanceReport.created_at.desc()).all()
    except OperationalError as error:
        if is_schema_mismatch_error(error):
            _raise_schema_mismatch_http_error(error)
        raise
    return reports

@router.get("/governance/reports/{id}", response_model=GovernanceReportResponse)
def get_governance_report(id: int, db: Session = Depends(get_db)):
    """Retrieves a single governance report by ID with nested details."""
    try:
        report = db.query(GovernanceReport).options(joinedload(GovernanceReport.document)).filter(GovernanceReport.id == id).first()
    except OperationalError as error:
        if is_schema_mismatch_error(error):
            _raise_schema_mismatch_http_error(error)
        raise
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Governance report not found")
    return report

@router.patch("/governance/reports/{id}/review", response_model=GovernanceReportResponse)
def review_governance_report(
    id: int,
    payload: ReportReviewRequest,
    db: Session = Depends(get_db)
):
    """Approves or requests changes for a report, driving the workflow job state."""
    try:
        report = db.query(GovernanceReport).filter(GovernanceReport.id == id).first()
    except OperationalError as error:
        if is_schema_mismatch_error(error):
            _raise_schema_mismatch_http_error(error)
        raise
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Governance report not found")
        
    # Update report fields
    report.reviewer = payload.reviewer
    report.review_status = payload.review_status
    report.review_notes = payload.review_notes
    report.updated_at = datetime.utcnow()
    
    # Drive Document/Job state based on action
    doc = db.query(Document).filter(Document.id == report.document_id).first()
    job = db.query(WorkflowJob).filter(WorkflowJob.document_id == report.document_id).order_by(WorkflowJob.id.desc()).first()
    
    audit_details = f"Review Notes: {payload.review_notes or 'None'}"
    
    if payload.review_status == "approved":
        # Report approved -> Published
        doc.status = WorkflowStatus.PUBLISHED
        if job:
            job.status = WorkflowStatus.PUBLISHED
        report.review_status = "approved"
        event_name = "Approved"
    else:
        # Changes requested -> Failed review state
        doc.status = WorkflowStatus.FAILED
        if job:
            job.status = WorkflowStatus.FAILED
        report.review_status = "changes_requested"
        event_name = "Changes Requested"
        
    # Record Audit entry
    audit = AuditLog(
        document_id=report.document_id,
        governance_report_id=report.id,
        event=event_name,
        user=payload.reviewer,
        details=f"Status: {payload.review_status}. {audit_details}"
    )
    
    db.add(audit)
    db.commit()
    db.refresh(report)
    
    logger.info(f"Report ID {report.id} reviewed. Status updated to {payload.review_status} by {payload.reviewer}")
    return report

@router.get("/governance/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Computes operational KPIs and lists recent audit log entries."""
    total_docs = db.query(Document).count()
    pending_reviews = db.query(GovernanceReport).filter(
        GovernanceReport.review_status == "pending_review",
        GovernanceReport.is_latest == True
    ).count()
    approved_reports = db.query(GovernanceReport).filter(
        GovernanceReport.review_status == "approved"
    ).count()
    failed_jobs = db.query(WorkflowJob).filter(
        WorkflowJob.status == WorkflowStatus.FAILED
    ).count()
    
    total_escalations = db.query(EscalationItem).count()
    open_escalations = db.query(EscalationItem).filter(
        EscalationItem.status == "open"
    ).count()
    
    # Averages
    avg_confidence = db.query(func.avg(GovernanceReport.confidence_score)).scalar() or 0.0
    avg_processing = db.query(func.avg(GovernanceReport.processing_time_seconds)).scalar() or 0.0
    total_tokens = db.query(func.sum(GovernanceReport.tokens_used)).scalar() or 0
    
    # Recent audits
    recent_audits = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(15).all()
    
    # Total reports generated
    reports_generated = db.query(GovernanceReport).count()
    
    return {
        "total_documents": total_docs,
        "pending_reviews": pending_reviews,
        "approved_reports": approved_reports,
        "failed_jobs": failed_jobs,
        "total_escalations": total_escalations,
        "open_escalations": open_escalations,
        "average_confidence": round(float(avg_confidence), 2),
        "average_processing_time": round(float(avg_processing), 2),
        "total_tokens_consumed": int(total_tokens),
        "reports_generated": reports_generated,
        "recent_logs": recent_audits
    }

@router.get("/governance/dashboard/charts", response_model=DashboardChartsResponse)
def get_dashboard_charts(db: Session = Depends(get_db)):
    """Returns aggregated chart data for the executive dashboard."""
    
    # Reports by review status
    reports_by_status_rows = (
        db.query(GovernanceReport.review_status, func.count(GovernanceReport.id))
        .group_by(GovernanceReport.review_status)
        .all()
    )
    reports_by_status = [
        {"label": status or "unknown", "count": count}
        for status, count in reports_by_status_rows
    ]
    
    # Escalations by severity
    esc_by_severity_rows = (
        db.query(EscalationItem.severity, func.count(EscalationItem.id))
        .group_by(EscalationItem.severity)
        .all()
    )
    escalations_by_severity = [
        {"label": severity or "unknown", "count": count}
        for severity, count in esc_by_severity_rows
    ]
    
    # RAID items distribution by type
    raid_dist_rows = (
        db.query(RaidItem.type, func.count(RaidItem.id))
        .group_by(RaidItem.type)
        .all()
    )
    raid_distribution = [
        {"label": raid_type or "unknown", "count": count}
        for raid_type, count in raid_dist_rows
    ]
    
    # Processing trend: reports created per day (last 30 days)
    trend_rows = (
        db.query(
            func.date(GovernanceReport.created_at).label("date"),
            func.count(GovernanceReport.id).label("count")
        )
        .group_by(func.date(GovernanceReport.created_at))
        .order_by(func.date(GovernanceReport.created_at))
        .all()
    )
    processing_trend = [
        {"date": str(row.date), "count": row.count}
        for row in trend_rows
    ]
    
    return {
        "reports_by_status": reports_by_status,
        "escalations_by_severity": escalations_by_severity,
        "raid_distribution": raid_distribution,
        "processing_trend": processing_trend
    }

@router.get("/governance/escalations", response_model=List[EscalationItemResponse])
def list_escalations(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists escalations, optionally filtered by status (open, routed)."""
    query = db.query(EscalationItem).options(
        joinedload(EscalationItem.report).joinedload(GovernanceReport.document)
    )
    if status:
        query = query.filter(EscalationItem.status == status)
    return query.order_by(EscalationItem.created_at.desc()).all()

@router.post("/governance/escalations/{id}/route", response_model=EscalationItemResponse)
def route_escalation(
    id: int,
    payload: EscalationRouteRequest,
    db: Session = Depends(get_db)
):
    """Routes an escalation item to a specified target stakeholder."""
    esc = db.query(EscalationItem).options(
        joinedload(EscalationItem.report).joinedload(GovernanceReport.document)
    ).filter(EscalationItem.id == id).first()
    if not esc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Escalation item not found")
        
    esc.status = "routed"
    esc.routing_target = payload.routing_target
    
    # Add Audit log
    report = db.query(GovernanceReport).filter(GovernanceReport.id == esc.report_id).first()
    doc_id = report.document_id if report else None
    
    audit = AuditLog(
        document_id=doc_id,
        governance_report_id=esc.report_id,
        event="Escalation Routed",
        user="reviewer_user",  # Actioned by reviewer
        details=f"Escalation routed to {payload.routing_target}. Issue: {esc.description[:100]}"
    )
    
    db.add(audit)
    db.commit()
    db.refresh(esc)
    
    logger.info(f"Escalation ID {esc.id} successfully routed to {payload.routing_target}")
    return esc

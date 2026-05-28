import logging
import traceback
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.models import (
    Document, WorkflowJob, WorkflowStatus, GovernanceReport, RaidItem, EscalationItem, MeetingAction, AuditLog
)
from backend.app.services.ingestion.parser import parse_file
from backend.app.services.ingestion.cleaner import clean_text
from backend.app.services.ingestion.chunker import chunk_text
from backend.app.services.rag.retrieval import RetrievalService
from backend.app.services.ai.ai_service import AIService

logger = logging.getLogger("governance_copilot.services.workflow")

def log_workflow_step(db: Session, job: WorkflowJob, message: str) -> None:
    """Appends timestamped message to the workflow job's execution logs."""
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}\n"
    job.logs += formatted_msg
    db.commit()

async def process_document_pipeline(document_id: int, job_id: int) -> None:
    """
    Executes the ingestion, indexing, retrieval, and AI extraction workflow.
    Designed to run inside a background thread.
    """
    db = SessionLocal()
    
    # Retrieve job and document
    job = db.query(WorkflowJob).filter(WorkflowJob.id == job_id).first()
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not job or not document:
        logger.error("Workflow job or document missing. Aborting.")
        db.close()
        return

    try:
        # 1. Update Status to PROCESSING
        logger.info(f"Starting pipeline for Document ID: {document.id}")
        document.status = WorkflowStatus.PROCESSING
        job.status = WorkflowStatus.PROCESSING
        db.commit()
        
        # Log to Audit
        audit = AuditLog(
            document_id=document.id,
            event="Processed",
            user="system",
            details="Workflow job processing pipeline initiated."
        )
        db.add(audit)
        db.commit()
        
        log_workflow_step(db, job, "Pipeline started. Parsing document...")
        
        # 2. Extract text from file path
        text = parse_file(str(document.filename), document.type)
        log_workflow_step(db, job, f"Successfully parsed document. Character count: {len(text)}")
        
        # 3. Clean Text
        cleaned_text = clean_text(text)
        log_workflow_step(db, job, "Text sanitized and control characters removed.")
        
        # 4. Deterministic overlapping chunking
        chunks = chunk_text(
            cleaned_text,
            document_id=document.id,
            filename=Path(document.filename).name,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        log_workflow_step(db, job, f"Text segmented into {len(chunks)} chunks.")
        
        # 5. Populate Search Index (RAG)
        RetrievalService.add_chunks(chunks)
        log_workflow_step(db, job, "Chunks indexed into TF-IDF vector storage.")
        
        # 6. Retrieve relevant context (RAG)
        context = ""
        if settings.USE_RAG:
            log_workflow_step(db, job, "Executing RAG context retrieval...")
            # Query for general project risks/escalations to build strong prompt context
            context_query = "project risks issues action items timeline status escalations dependencies"
            context = RetrievalService.retrieve_relevant_context(
                query=context_query,
                document_id=document.id,
                top_k=3
            )
            log_workflow_step(db, job, f"RAG context compiled. Retrieved context size: {len(context)}")
        else:
            log_workflow_step(db, job, "RAG retrieval bypassed by configuration flag.")
            
        # 7. AI Processing
        log_workflow_step(db, job, "Invoking AI service for structured data extraction...")
        ai_service = AIService()
        
        # Call provider and validate
        ai_results = await ai_service.analyze_governance_document(cleaned_text, context)
        log_workflow_step(db, job, f"AI extractions completed. Confidence score: {ai_results['confidence_score']:.2f}")
        
        # 8. Report Versioning Lifecycle
        # Find if a previous report exists for this document
        existing_reports = db.query(GovernanceReport).filter(
            GovernanceReport.document_id == document.id
        ).order_by(GovernanceReport.version.desc()).all()
        
        next_version = 1
        if existing_reports:
            # Deprecate older report active statuses
            for report in existing_reports:
                report.is_latest = False
            next_version = existing_reports[0].version + 1
            log_workflow_step(db, job, f"Previous report found. Archiving V{existing_reports[0].version}. Generating V{next_version}...")
            
        # 9. Store governance report data
        report = GovernanceReport(
            document_id=document.id,
            summary=ai_results["summary"],
            executive_summary=ai_results["executive_summary"],
            confidence_score=ai_results["confidence_score"],
            model_version=settings.AI_PROVIDER,  # Store provider name
            prompt_version="v1",
            review_status="pending_review",
            processing_time_seconds=ai_results["processing_time_seconds"],
            tokens_used=ai_results["tokens_used"],
            provider_name=ai_results["provider_name"],
            version=next_version,
            is_latest=True,
            document_type=ai_results.get("document_type", "generic_business_document"),
            classification_confidence=ai_results.get("classification_confidence", 0.5),
            governance_relevance=ai_results.get("governance_relevance", "medium")
        )
        db.add(report)
        db.commit()  # Committing allows us to obtain report.id
        
        # Write RAID Items
        for r in ai_results["raid_items"]:
            raid_item = RaidItem(
                report_id=report.id,
                type=r["type"],
                description=r["description"],
                severity=r["severity"],
                confidence_score=r["confidence_score"],
                source_excerpt=r["source_excerpt"]
            )
            db.add(raid_item)
            
        # Write Escalations
        for esc in ai_results["escalation_items"]:
            escalation_item = EscalationItem(
                report_id=report.id,
                description=esc["description"],
                severity=esc["severity"],
                status="open",
                source_excerpt=esc["source_excerpt"],
                confidence_score=esc["confidence_score"]
            )
            db.add(escalation_item)
            
        # Write Meeting Actions
        for action in ai_results.get("meeting_actions", []):
            meeting_action = MeetingAction(
                report_id=report.id,
                owner=action["owner"],
                task=action["task"],
                due_date=action.get("due_date")
            )
            db.add(meeting_action)
            
        db.commit()
        log_workflow_step(db, job, f"Structured RAID, Escalation, and Meeting Action items persisted to database. Report ID: {report.id}")
        
        # 10. Update Status to PENDING_REVIEW
        document.status = WorkflowStatus.PENDING_REVIEW
        job.status = WorkflowStatus.PENDING_REVIEW
        
        audit_success = AuditLog(
            document_id=document.id,
            governance_report_id=report.id,
            event="Review Pending",
            user="system",
            details=f"Governance Report V{next_version} created. Review Queue updated."
        )
        db.add(audit_success)
        
        log_workflow_step(db, job, "Pipeline completed successfully. Awaiting reviewer action.")
        db.commit()
        
    except Exception as e:
        # Failure recovery
        error_msg = f"Pipeline execution failed: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # Clean up session rollback
        db.rollback()
        
        try:
            # Mark document and job as FAILED
            document.status = WorkflowStatus.FAILED
            job.status = WorkflowStatus.FAILED
            
            # Save stack trace to job logs
            log_workflow_step(db, job, f"ERROR: {error_msg}")
            log_workflow_step(db, job, f"TRACEBACK:\n{traceback.format_exc()}")
            
            # Log failure in Audit Trail
            audit_fail = AuditLog(
                document_id=document.id,
                event="Failed",
                user="system",
                details=f"Processing pipeline execution aborted. Reason: {str(e)[:200]}"
            )
            db.add(audit_fail)
            db.commit()
        except Exception as nested_err:
            logger.critical(f"Failed to record pipeline failure state: {nested_err}")
            
    finally:
        db.close()

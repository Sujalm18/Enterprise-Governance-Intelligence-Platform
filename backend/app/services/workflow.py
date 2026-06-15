import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import SessionLocal
from backend.app.models import (
    Document, WorkflowJob, WorkflowStatus, GovernanceReport, RaidItem, EscalationItem, MeetingAction, AuditLog, Notification
)
from backend.app.services.ingestion.parser import parse_file
from backend.app.services.ingestion.cleaner import clean_text
from backend.app.services.rag.chunker import chunk_document_semantically
from backend.app.services.rag.retrieval import RetrievalService
from backend.app.services.ai.ai_service import AIService
from backend.app.services.governance.playbook import PlaybookEngine

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
        
        chunks = chunk_document_semantically(
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
            governance_relevance=ai_results.get("governance_relevance", "medium"),
            
            # Workflow Automated Assignment
            created_by="Analyst",
            assigned_to="Manager",
            status="PENDING_MANAGER_REVIEW",
            tenant_id=document.tenant_id
        )
        db.add(report)
        db.commit()  # Committing allows us to obtain report.id
        
        # Create notification for Manager
        notif_report = Notification(
            severity="MEDIUM",
            notification_type="REPORT_PENDING_REVIEW",
            title="New Governance Report Pending Review",
            message=f"Governance Report V{next_version} for '{report.filename}' is pending review.",
            recipient_role="Manager",
            related_entity_type="report",
            related_entity_id=report.id,
            read_status=False,
            tenant_id=document.tenant_id
        )
        db.add(notif_report)
        db.commit()
        
        # Write RAID Items
        raid_items_to_create = []
        for r in ai_results["raid_items"]:
            # Enrich RAID item with deterministic Playbook Engine
            enriched_r = PlaybookEngine.enrich_raid_item(r, relevance=report.governance_relevance)
            
            raid_item = RaidItem(
                report_id=report.id,
                type=enriched_r["type"],
                description=enriched_r["description"],
                severity=enriched_r["severity"],
                confidence_score=enriched_r["confidence_score"],
                source_excerpt=enriched_r["source_excerpt"],
                
                # Phase 2 Decision Support columns
                recommended_mitigations=json.dumps(enriched_r["recommended_mitigations"]) if isinstance(enriched_r["recommended_mitigations"], list) else enriched_r["recommended_mitigations"],
                implementation_effort=enriched_r["implementation_effort"],
                expected_risk_reduction=enriched_r["expected_risk_reduction"],
                recommended_priority=enriched_r["recommended_priority"],
                suggested_owner_role=enriched_r["suggested_owner_role"],
                priority=enriched_r["priority"],
                risk_score=enriched_r["risk_score"],
                current_risk_score=enriched_r["risk_score"], # Initial residual risk is equal to original risk
                explainability_trace=enriched_r["explainability_trace"],
                
                # Priority 1 & 5 Additions
                explain_why=enriched_r.get("explain_why"),
                suggested_actions=enriched_r.get("suggested_actions"),
                estimated_impact=enriched_r.get("estimated_impact"),
                tenant_id=document.tenant_id
            )
            db.add(raid_item)
            raid_items_to_create.append((raid_item, enriched_r))
            
        db.commit() # Commit to get raid_item.id values
        
        try:
            from backend.app.services.integrations import trigger_governance_alerts
            for raid_item, _ in raid_items_to_create:
                if raid_item.priority == "P1":
                    trigger_governance_alerts(
                        db=db,
                        tenant_id=document.tenant_id or 1,
                        title=f"New P1 Risk Identified: {raid_item.type.upper()}",
                        message=f"A new P1 {raid_item.type} was detected: '{raid_item.description}'",
                        severity="high",
                        details=f"Suggested Owner Role: {raid_item.suggested_owner_role}\nRisk Score: {raid_item.risk_score}"
                    )
        except Exception as alert_err:
            logger.error(f"Failed to trigger RAID alert webhooks: {alert_err}")
        
        # Now create MitigationTasks for each recommendation
        from datetime import timedelta
        for raid_item, enriched_r in raid_items_to_create:
            mitigations = enriched_r.get("recommended_mitigations") or []
            if isinstance(mitigations, str):
                try:
                    mitigations = json.loads(mitigations)
                except Exception:
                    mitigations = [mitigations]
                    
            # Only create for risk and issue items
            if raid_item.type.lower() in {"risk", "issue"}:
                for mit in mitigations:
                    # Default effectiveness based on priority
                    p = raid_item.priority or "P4"
                    eff_map = {"P1": 30, "P2": 20, "P3": 15, "P4": 10}
                    eff = eff_map.get(p, 20)
                    
                    # Target date in 14 days
                    target_dt = (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d")
                    
                    # Create MitigationTask
                    from backend.app.models import MitigationTask
                    task = MitigationTask(
                        title=mit,
                        description=f"Automatically generated mitigation task for: {raid_item.description}",
                        related_raid_item_id=raid_item.id,
                        related_escalation_id=None,
                        owner_role=raid_item.suggested_owner_role or "Analyst",
                        owner_name=None,
                        priority=p,
                        risk_score=raid_item.risk_score,
                        target_date=target_dt,
                        sla_status="ON_TRACK",
                        status="PLANNED",
                        completion_percentage=0,
                        effectiveness=eff,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                        tenant_id=document.tenant_id
                    )
                    db.add(task)
                    db.commit() # get task.id
                    
                    # Create notification for Mitigation owner
                    notif_task = Notification(
                        severity="LOW" if p in ("P3", "P4") else "MEDIUM",
                        notification_type="MITIGATION_ASSIGNED",
                        title="New Mitigation Task Assigned",
                        message=f"Mitigation task '{task.title}' has been assigned to you.",
                        recipient_role=task.owner_role,
                        related_entity_type="mitigation",
                        related_entity_id=task.id,
                        read_status=False,
                        tenant_id=document.tenant_id
                    )
                    db.add(notif_task)
                    db.commit()
                    
                    # Log Audit Event
                    audit_task = AuditLog(
                        document_id=document.id,
                        governance_report_id=report.id,
                        event="MITIGATION_CREATED",
                        user="system",
                        user_role="Analyst",
                        action="mitigation creation",
                        entity_type="mitigation",
                        entity_id=task.id,
                        details=f"Mitigation task '{task.title[:60]}' created and assigned to {task.owner_role}.",
                        tenant_id=document.tenant_id
                    )
                    db.add(audit_task)
                    db.commit()
            
        # Write Escalations
        for esc in ai_results["escalation_items"]:
            # Enrich Escalation item with deterministic Playbook Engine
            enriched_esc = PlaybookEngine.enrich_escalation_item(esc, relevance=report.governance_relevance)
            
            escalation_item = EscalationItem(
                report_id=report.id,
                description=enriched_esc["description"],
                severity=enriched_esc["severity"],
                status="ASSIGNED",
                routing_target="Governance Lead",
                source_excerpt=enriched_esc["source_excerpt"],
                confidence_score=enriched_esc["confidence_score"],
                
                # Workflow Automated Assignment
                raised_by="Analyst",
                assigned_to="Governance Lead",
                
                # Phase 2 Decision Support columns
                remediation_plan=enriched_esc["remediation_plan"],
                expected_risk_reduction=enriched_esc["expected_risk_reduction"],
                priority=enriched_esc["priority"],
                suggested_owner_role=enriched_esc["suggested_owner_role"],
                risk_score=enriched_esc["risk_score"],
                explainability_trace=enriched_esc["explainability_trace"],
                
                # Priority 1 & 5 Additions
                explain_why=enriched_esc.get("explain_why"),
                suggested_actions=enriched_esc.get("suggested_actions"),
                estimated_impact=enriched_esc.get("estimated_impact"),
                tenant_id=document.tenant_id
            )
            db.add(escalation_item)
            db.commit() # Commit to get escalation_item.id
            
            try:
                from backend.app.services.integrations import trigger_governance_alerts
                if escalation_item.severity in ("critical", "high") or escalation_item.priority == "P1":
                    trigger_governance_alerts(
                        db=db,
                        tenant_id=document.tenant_id or 1,
                        title="Critical Escalation Raised",
                        message=f"Escalation item raised: '{escalation_item.description}'",
                        severity="critical",
                        details=f"Routing target: {escalation_item.routing_target}\nSeverity: {escalation_item.severity.upper()}"
                    )
            except Exception as alert_err:
                logger.error(f"Failed to trigger escalation alert webhooks: {alert_err}")

            # Create notification for Governance Lead
            notif_esc = Notification(
                severity="HIGH" if escalation_item.severity in ("critical", "high") else "MEDIUM",
                notification_type="ESCALATION_ASSIGNED",
                title="New Escalation Assigned",
                message=f"New escalation item assigned to you: '{escalation_item.description[:100]}'.",
                recipient_role="Governance Lead",
                related_entity_type="escalation",
                related_entity_id=escalation_item.id,
                read_status=False,
                tenant_id=document.tenant_id
            )
            db.add(notif_esc)
            db.commit()
            
            # Log Escalation Creation Event
            audit_esc = AuditLog(
                document_id=document.id,
                governance_report_id=report.id,
                event="Escalation Created",
                user="system",
                user_role="Analyst",
                action="escalation creation",
                entity_type="escalation",
                entity_id=escalation_item.id,
                details=f"Escalation item created and assigned to Governance Lead. Description: {esc['description'][:100]}"
            )
            db.add(audit_esc)
            
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
            user_role="Analyst",
            action="AI report generation",
            entity_type="report",
            entity_id=report.id,
            details=f"Governance Report V{next_version} generated automatically by AI and assigned to Manager."
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

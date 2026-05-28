import os
import sys
import tempfile
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set database URL override before loading database module
temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
os.close(temp_db_fd)
os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path}"

# Now import the app and other components
from backend.app.main import app
from backend.app.database import Base, get_db, init_db
from backend.app.config import settings
from backend.app.models import (
    User, Document, GovernanceReport, EscalationItem, AuditLog, WorkflowStatus, WorkflowJob
)

def run_verification():
    print("=" * 60)
    print("      Enterprise AI Traceability Verification Script")
    print("=" * 60)
    
    # 1. Initialize DB
    print("[+] Initializing database tables...")
    engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    # Seed users
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    analyst = User(username="analyst_user", role="analyst")
    reviewer = User(username="reviewer_user", role="reviewer")
    db.add(analyst)
    db.add(reviewer)
    db.commit()
    db.close()
    
    # Prepare FastAPI test client
    client = TestClient(app)
    
    # Files to verify - tuple: (filename, filepath, content_type, expects_report)
    test_files = [
        ("project_status.txt.txt", "testing files/project_status.txt.txt", "text/plain", True),
        ("world bank.pdf", "testing files/world bank.pdf", "application/pdf", False)  # Scanned PDF, no extractable text
    ]
    
    for filename, filepath, content_type, expects_report in test_files:
        print(f"\n--- Testing File: {filename} ---")
        
        path = Path(filepath)
        if not path.exists():
            print(f"[!] Warning: Test file not found at {filepath}. Skipping.")
            continue
            
        with open(path, "rb") as f:
            file_bytes = f.read()
            
        # 1. Test Upload
        print("[+] Uploading document...")
        upload_resp = client.post(
            "/api/upload",
            files={"file": (filename, file_bytes, content_type)},
            params={"use_rag": False}
        )
        assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
        upload_data = upload_resp.json()
        doc_id = upload_data["id"]
        clean_uploaded_name = upload_data["filename"]
        
        print(f"    Uploaded Filename (cleaned): '{clean_uploaded_name}'")
        assert clean_uploaded_name == filename, f"Expected '{filename}' but got '{clean_uploaded_name}'"
        
        # --- Branch: Scanned/Unparseable files (no report expected) ---
        if not expects_report:
            print("[+] This file is expected to fail parsing (scanned PDF). Verifying failure handling...")
            
            # Verify the document status is FAILED
            doc_resp = client.get(f"/api/workflow/jobs/{doc_id}")
            if doc_resp.status_code == 200:
                job_data = doc_resp.json()
                print(f"    Job Status: '{job_data['status']}'")
                assert job_data["status"] == "failed", f"Expected 'failed' but got '{job_data['status']}'"
                print(f"    [OK] Document correctly marked as FAILED.")
            
            # Verify audit trail records the failure
            stats_resp = client.get("/api/governance/dashboard/stats")
            assert stats_resp.status_code == 200
            stats = stats_resp.json()
            recent_logs = stats["recent_logs"]
            doc_events = [log for log in recent_logs if log["document_id"] == doc_id]
            print(f"    Found {len(doc_events)} audit events for Document ID {doc_id}:")
            for log in doc_events:
                print(f"      - {log['timestamp'][:19]} | Event: {log['event']} | Actor: {log['user']} | Details: {log['details']}")
            
            assert any(log["event"] == "Uploaded" for log in doc_events), "Missing Uploaded audit log!"
            assert any(log["event"] == "Failed" for log in doc_events), "Missing Failed audit log!"
            print(f"    [OK] Scanned PDF traceability verified: Upload -> Failed (with audit trail).")
            continue
        
        # --- Branch: Parseable files (full traceability check) ---
        # FastAPI's TestClient runs background tasks synchronously, so the report should be created immediately.
        # 2. Verify report generated
        print("[+] Retrieving generated report...")
        reports_resp = client.get("/api/governance/reports", params={"is_latest": True})
        assert reports_resp.status_code == 200
        reports = reports_resp.json()
        
        # Find the report for this document
        doc_reports = [r for r in reports if r["document_id"] == doc_id]
        assert len(doc_reports) > 0, "No report found for uploaded document!"
        report = doc_reports[0]
        report_id = report["id"]
        
        print(f"    Report ID: {report_id}")
        print(f"    Report Filename: '{report['filename']}'")
        assert report["filename"] == filename, f"Expected report filename to be '{filename}' but got '{report['filename']}'"
        
        # 3. Test Review Queue Retrieval
        print("[+] Verifying in Review Queue...")
        pending_resp = client.get("/api/governance/reports", params={"is_latest": True, "review_status": "pending_review"})
        assert pending_resp.status_code == 200
        pending_reports = pending_resp.json()
        pending_matching = [r for r in pending_reports if r["id"] == report_id]
        assert len(pending_matching) == 1, "Report not visible in pending review queue!"
        pending_rep = pending_matching[0]
        print(f"    Review Queue Filename: '{pending_rep['filename']}'")
        assert pending_rep["filename"] == filename, "Filename mismatch in pending review queue!"
        
        # 4. Test Submission of Review (Approve)
        print("[+] Submitting approval review...")
        review_payload = {
            "reviewer": "reviewer_user",
            "review_status": "approved",
            "review_notes": "All checks verified successfully."
        }
        review_resp = client.patch(f"/api/governance/reports/{report_id}/review", json=review_payload)
        assert review_resp.status_code == 200
        reviewed_report = review_resp.json()
        print(f"    Approved Report Filename: '{reviewed_report['filename']}'")
        assert reviewed_report["filename"] == filename, "Filename mismatch in approved review response!"
        
        # 5. Test Escalation item mapping and filename
        print("[+] Listing escalations...")
        esc_resp = client.get("/api/governance/escalations")
        assert esc_resp.status_code == 200
        escalations = esc_resp.json()
        
        # Find escalations for our report
        doc_escalations = [e for e in escalations if e["report_id"] == report_id]
        if doc_escalations:
            print(f"    Found {len(doc_escalations)} escalations.")
            for esc in doc_escalations:
                print(f"      Escalation ID #{esc['id']} - Filename: '{esc['filename']}' - Status: '{esc['status']}'")
                assert esc["filename"] == filename, "Filename mismatch in escalation item!"
                
                # Test routing the escalation
                print(f"      [+] Routing Escalation #{esc['id']}...")
                route_resp = client.post(
                    f"/api/governance/escalations/{esc['id']}/route",
                    json={"routing_target": "Steering Committee"}
                )
                assert route_resp.status_code == 200
                routed_esc = route_resp.json()
                assert routed_esc["status"] == "routed"
                assert routed_esc["routing_target"] == "Steering Committee"
                assert routed_esc["filename"] == filename, "Filename mismatch in routed escalation response!"
        else:
            print("    No escalations found for this report (Optional, based on text content).")
            
        # 6. Verify Audit Logs Traceability
        print("[+] Verifying Audit Log Entries...")
        stats_resp = client.get("/api/governance/dashboard/stats")
        assert stats_resp.status_code == 200
        stats = stats_resp.json()
        recent_logs = stats["recent_logs"]
        
        # Find events related to our document
        doc_events = [log for log in recent_logs if log["document_id"] == doc_id]
        print(f"    Found {len(doc_events)} audit events for Document ID {doc_id}:")
        for log in doc_events:
            print(f"      - {log['timestamp'][:19]} | Event: {log['event']} | Actor: {log['user']} | Details: {log['details']}")
            
        assert any(log["event"] == "Uploaded" for log in doc_events), "Missing Uploaded audit log!"
        assert any(log["event"] == "Processed" for log in doc_events), "Missing Processed audit log!"
        assert any(log["event"] == "Approved" for log in doc_events), "Missing Approved audit log!"
        if doc_escalations:
            assert any(log["event"] == "Escalation Routed" for log in doc_events), "Missing Escalation Routed audit log!"
            
    print("\n" + "=" * 60)
    print("   Traceability Verification Completed Successfully!")
    print("=" * 60)

    # Cleanup temp db
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except Exception:
            pass

if __name__ == "__main__":
    try:
        run_verification()
    except AssertionError as e:
        print(f"\n[!] Verification FAILED: {e}")
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except Exception:
                pass
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Unexpected Error during verification: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(temp_db_path):
            try:
                os.remove(temp_db_path)
            except Exception:
                pass
        sys.exit(1)

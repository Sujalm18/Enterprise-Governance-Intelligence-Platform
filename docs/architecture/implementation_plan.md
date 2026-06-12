# Enterprise AI Governance & Operations Copilot Implementation Plan (Final Refined)

This implementation plan details the updated MVP design incorporating your critical recommendations for cleaner abstractions, reliable vector-less TF-IDF retrieval, validation layers, audit trails, simplified roles, operational metadata logging, type-safe workflow state management, prompt versioning, and report versioning.

## User Review Required

> [!IMPORTANT]
> - **AI Provider abstraction** is built under `services/ai/` supporting Anthropic and a Mock Provider out-of-the-box.
> - **Zero-dependency RAG** is achieved via a custom Python TF-IDF and Cosine Similarity service. This ensures instant deployment on all Windows configurations.
> - **Audit Trail** (`AuditLog` database table) is introduced to record every operational step (e.g. Upload, Review, Escalation Routing).
> - **Schema Validation** is enforced using Pydantic validation before saving any AI responses.
> - **Simple Roles** are constrained to `analyst` and `reviewer`.
> - **Operational Metrics**: Every generated report tracks `processing_time_seconds`, `tokens_used`, and `provider_name`.
> - **Type-safe Workflow States**: Defined using a strict `WorkflowStatus` Enum that supports error/failed states for handles like PDF corruption or API timeouts.
> - **Prompt Versioning**: Prompt templates are stored in a dedicated `backend/app/prompts/` directory to allow easy versioning (`v1`, `v2`, etc.).
> - **Report Versioning**: The `GovernanceReport` table includes `version` (int) and `is_latest` (bool) fields, enabling users to request changes, re-generate documents, and preserve historical report states.

## Proposed Changes

### Directory Structure

```
c:\Users\10651.PHNTECHNOLOGY\Desktop\Projects\Enterprise AI\
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── logging_config.py
│   │   ├── prompts/
│   │   │   ├── governance_v1.txt
│   │   │   ├── raid_v1.txt
│   │   │   └── escalation_v1.txt
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── endpoints.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── ingestion/
│   │       │   ├── __init__.py
│   │       │   ├── parser.py
│   │       │   ├── cleaner.py
│   │       │   └── chunker.py
│   │       ├── rag/
│   │       │   ├── __init__.py
│   │       │   └── retrieval.py
│   │       ├── ai/
│   │       │   ├── __init__.py
│   │       │   ├── provider.py
│   │       │   ├── anthropic_provider.py
│   │       │   ├── mock_provider.py
│   │       │   └── ai_service.py
│   │       └── workflow.py
├── frontend/
│   ├── app.py
│   └── pages/
│       ├── 1_Dashboard.py
│       ├── 2_Upload_Center.py
│       ├── 3_Governance_Reports.py
│       ├── 4_Review_Queue.py
│       ├── 5_Escalations.py
│       └── 6_Workflow_Tracker.py
├── data/
│   ├── uploads/ (created dynamically)
│   └── sample/  (demo data files)
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_ai.py
│   ├── test_workflow.py
│   └── test_api.py
├── requirements.txt
├── run.py
├── README.md
├── architecture.md
├── deployment_guide.md
└── github_release_checklist.md
```

---

### Component-by-Component Blueprint

#### 1. Configuration & Prompt Management

##### [MODIFY] [config.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/config.py)
Stores:
- `CHUNK_SIZE` (Default: 1000)
- `CHUNK_OVERLAP` (Default: 200)
- `USE_RAG` (Default: True)
- `USE_MOCK_MODE` (Default: True if `ANTHROPIC_API_KEY` is missing)
- `AI_PROVIDER` (Default: "anthropic" or "mock")
- SQLite Database URL (`sqlite:///./data/governance.db`)
- Ingestion folder path (`./data/uploads`)

##### [NEW] Prompt Templates
Stored in `backend/app/prompts/` for easy iteration:
- `governance_v1.txt`: System instructions for extracting high-level summaries.
- `raid_v1.txt`: Guidelines on locating risks, actions, issues, and dependencies.
- `escalation_v1.txt`: Direct instructions on identifying overdue milestones and executive concerns.

#### 2. Database Models & Schema Verification

##### [MODIFY] [models.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/models.py)
Enforces a Python enum for job status, tracks key operational metrics, and version-controls report iterations:
- **WorkflowStatus Enum**:
  - `UPLOADED` = "uploaded"
  - `PROCESSING` = "processing"
  - `PENDING_REVIEW` = "pending_review"
  - `APPROVED` = "approved"
  - `PUBLISHED` = "published"
  - `FAILED` = "failed"
- **AuditLog**: `id`, `document_id`, `governance_report_id`, `event`, `user`, `details`, `timestamp`
- **Document**: `id`, `filename`, `type`, `status` (WorkflowStatus)
- **WorkflowJob**: `id`, `document_id`, `status` (WorkflowStatus), `logs`, `updated_at`
- **GovernanceReport**: `id`, `document_id`, `summary`, `executive_summary`, `confidence_score`, `model_version`, `review_status`, `reviewer`, `review_notes`, `processing_time_seconds` (Float), `tokens_used` (Int), `provider_name` (Str), `version` (Int, Default 1), `is_latest` (Bool, Default True)
- **RaidItem**: `id`, `report_id`, `type` (Risk/Action/Issue/Dependency), `description`, `severity`, `confidence_score`, `source_excerpt`
- **EscalationItem**: `id`, `report_id`, `description`, `severity`, `status` (open/routed), `routing_target`, `source_excerpt`, `confidence_score`
- **User**: Simulates two roles: `analyst` and `reviewer`.

##### [NEW] [schemas.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/schemas.py)
Declares Pydantic validation schemas to map client payloads:
- `ReportReviewRequest`
- `EscalationRouteRequest`
- `WorkflowJobStatusResponse`
- `AIReportExtractionSchema`: Validates LLM structural return values (`summary`, `executive_summary`, `raid_items`, `escalation_items`, `confidence_score`, `tokens_used`).

#### 3. AI Service Provider Layer

##### [NEW] [provider.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/services/ai/provider.py)
Abstract base class `AIProvider`:
- `async def extract_governance_data(self, text: str, context: str) -> dict`

##### [NEW] [anthropic_provider.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/services/ai/anthropic_provider.py)
Formats a structured prompt for Claude with system instructions, forcing strict JSON response, and invokes the Anthropic API. Returns metrics such as tokens used.

##### [NEW] [mock_provider.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/services/ai/mock_provider.py)
Extracts key terms from the document text (like Project Names, Dates, Vendor names) and builds a highly realistic, context-specific JSON output. Incorporates custom confidence scores, mock processing time, and token metrics.

##### [NEW] [ai_service.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/services/ai/ai_service.py)
Orchestrator class. Resolves which provider instance to use. Validates outputs against `AIReportExtractionSchema` and returns validated dictionaries or attempts error correction/fallbacks.

#### 4. Retrieval Layer (Lightweight TF-IDF)

##### [NEW] [retrieval.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/services/rag/retrieval.py)
A pure-Python TF-IDF Vectorizer and Cosine Similarity implementation. Tokenizes text, computes term frequencies and inverse document frequencies across document chunks, and ranks chunks against query strings to extract relevant context.

#### 5. Pipeline Workflow Worker

##### [NEW] [workflow.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/services/workflow.py)
Coordinates background execution:
1. Parse document (`parser.py`).
2. Clean text (`cleaner.py`).
3. Generate chunks (`chunker.py`).
4. Perform TF-IDF indexing.
5. Retrieve relevant chunks (if `USE_RAG` is active).
6. Send text context to the `AIService` and record start timestamp.
7. Validate the output JSON. Compute duration.
8. Store `GovernanceReport`, `RaidItem` list, and `EscalationItem` list in the DB. If a report already exists for the document, mark previous versions as `is_latest = False` and insert the new one with incremented `version`.
9. Write audit entries to `AuditLog`.
10. In case of failure, transition job status to `FAILED`, capture stack trace in workflow logs, and log the failure event in `AuditLog`.

#### 6. API Endpoints

##### [NEW] [endpoints.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/backend/app/api/endpoints.py)
Includes:
- `POST /upload`
- `GET /workflow/jobs/{id}`
- `GET /governance/reports`
- `GET /governance/reports/{id}`
- `PATCH /governance/reports/{id}/review` -> Enforces transitions and logs to `AuditLog`.
- `GET /governance/dashboard/stats` -> Returns KPI data, including processing metrics aggregates.
- `GET /governance/escalations`
- `POST /governance/escalations/{id}/route` -> Updates route target and writes to `AuditLog`.

#### 7. Frontend UI Pages (React)

##### [NEW] [app.py](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/frontend/app.py)
Configures high-end Dark/Steel Blue CSS style, custom fonts, side navigation, and simulated role selector (Analyst vs. Reviewer).

##### [NEW] [pages/](file:///c:/Users/10651.PHNTECHNOLOGY/Desktop/Projects/Enterprise%20AI/frontend/pages/)
- **1_Dashboard.py**: Displays summary statistics (Approval rate, Open Escalations, Average AI Confidence, Average Processing Time, Token Consumption charts) and lists the latest `AuditLog` entries.
- **2_Upload_Center.py**: Interactive upload interface with configuration overrides (chunk size, overlap, mock-mode override, RAG toggle).
- **3_Governance_Reports.py**: Filter and read details of approved and published reports. Supports toggling between report versions.
- **4_Review_Queue.py**: Allows Reviewers to browse reports in `pending_review`, examine their parsed RAID/Escalation details, write notes, and click Approve or Request Changes. Shows metrics: time taken, tokens used, provider.
- **5_Escalations.py**: Displays open risk issues and allows Routing to specific stakeholders (e.g. Steering Committee, PMO Lead).
- **6_Workflow_Tracker.py**: View processing logs for active/failed workflow jobs.

---

## Verification Plan

### Automated Tests
Execute using:
```bash
pytest tests/
```
Files to implement under `tests/`:
- `test_ingestion.py`: Tests document parser (TXT, PDF, Word), character cleaning, and overlapping chunks.
- `test_ai.py`: Validates the `MockProvider` and `AnthropicProvider` structures, response schemas, and mock generation reliability.
- `test_workflow.py`: Simulates end-to-end background job execution from uploaded files to database storage, verifying `AuditLog` triggers and version incrementing.
- `test_api.py`: Validates router inputs and HTTP responses.

### Manual Verification
- Start services via `python run.py`.
- Ingest a sample docx file on the `Upload Center` tab.
- Track execution status in `Workflow Tracker`.
- Review the generated content in the `Review Queue` under the Reviewer role. Check that confidence badges (e.g. 92%) are formatted clearly.
- Action an escalation routing in the `Escalations` center, and inspect the `AuditLog` on the `Dashboard` to confirm historical records.

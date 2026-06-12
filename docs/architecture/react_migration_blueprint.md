# React Migration Blueprint

> Note: Migration to React + Vite + TypeScript is complete; this document remains as a historical blueprint and mapping reference.

## Objective

Migrate the presentation layer from Streamlit to a modern React, TypeScript, Vite, Tailwind CSS, and shadcn/ui frontend while preserving the FastAPI backend, AI extraction engine, OCR pipeline, governance ontology, database models, regression framework, and public API behavior.

No backend extraction logic should be rewritten as part of this migration.

## Current Backend Inventory

### FastAPI Application

| Area | Current Location | Notes |
| --- | --- | --- |
| App entrypoint | `backend/app/main.py` | Creates FastAPI app, configures CORS, mounts `/api` router, exposes health endpoints. |
| API routes | `backend/app/api/endpoints.py` | Upload, workflow, reports, review, dashboard, escalations. |
| Database setup | `backend/app/database.py` | SQLAlchemy engine/session/base and startup initialization. |
| Settings | `backend/app/config.py` | Pydantic settings, database URL, upload paths, AI provider flags. |
| Models | `backend/app/models.py` | SQLAlchemy schema. |
| Response/request schemas | `backend/app/schemas.py` | Pydantic API contracts. |
| Workflow orchestration | `backend/app/services/workflow.py` | Background processing pipeline. |
| AI extraction | `backend/app/services/ai/` | Provider abstraction and governance extraction logic. |
| OCR/ingestion | `backend/app/services/ingestion/` | PDF/DOCX/TXT/XLSX parsing and OCR fallback. |

## Complete API Inventory

### Root and Health

| Method | Path | Request | Response | Current UI Usage | Must Preserve |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/` | None | `{status, app_name, active_provider, mock_mode_active}` | Not used by Streamlit pages | Yes |
| `GET` | `/health` | None | `{status, service, provider, mock_mode_active}` | Deployment health checks | Yes |

### Upload and Workflow

| Method | Path | Request | Response | Current UI Usage | Must Preserve |
| --- | --- | --- | --- | --- | --- |
| `POST` | `/api/upload` | Multipart `file`; optional query params `chunk_size`, `chunk_overlap`, `use_rag` | `DocumentResponse` | Upload Center | Yes |
| `GET` | `/api/workflow/jobs/{id}` | Path `id` | `WorkflowJobResponse` | Available, not strongly used by current workflow page | Yes |

### Governance Reports

| Method | Path | Request | Response | Current UI Usage | Must Preserve |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/governance/reports` | Query `is_latest: bool = true`, optional `review_status` | `List[GovernanceReportResponse]` | Dashboard-adjacent workflows, report list, review queue, workflow tracker | Yes |
| `GET` | `/api/governance/reports/{id}` | Path `id` | `GovernanceReportResponse` | Workflow tracker report detail | Yes |
| `PATCH` | `/api/governance/reports/{id}/review` | `ReportReviewRequest` | `GovernanceReportResponse` | Review Queue approve/request changes | Yes |

### Dashboard

| Method | Path | Request | Response | Current UI Usage | Must Preserve |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/governance/dashboard/stats` | None | `DashboardStatsResponse` | Dashboard KPI cards and audit log | Yes |
| `GET` | `/api/governance/dashboard/charts` | None | `DashboardChartsResponse` | Not currently used in Streamlit pages, but available for React charts | Yes |

### Escalations

| Method | Path | Request | Response | Current UI Usage | Must Preserve |
| --- | --- | --- | --- | --- | --- |
| `GET` | `/api/governance/escalations` | Optional query `status` | `List[EscalationItemResponse]` | Escalation Management page | Yes |
| `POST` | `/api/governance/escalations/{id}/route` | `EscalationRouteRequest` | `EscalationItemResponse` | Escalation routing form | Yes |

## API Schema Inventory

### Enums

`WorkflowStatus` values:

- `uploaded`
- `processing`
- `pending_review`
- `approved`
- `published`
- `failed`

### Response Schemas

#### `DocumentResponse`

| Field | Type |
| --- | --- |
| `id` | `int` |
| `filename` | `str` |
| `type` | `str` |
| `upload_timestamp` | `datetime` |
| `status` | `WorkflowStatus` |

#### `WorkflowJobResponse`

| Field | Type |
| --- | --- |
| `id` | `int` |
| `document_id` | `int` |
| `status` | `WorkflowStatus` |
| `logs` | `str` |
| `updated_at` | `datetime` |

#### `RaidItemResponse`

| Field | Type |
| --- | --- |
| `id` | `int` |
| `report_id` | `int` |
| `type` | `str` |
| `description` | `str` |
| `severity` | `str` |
| `confidence_score` | `float` |
| `source_excerpt` | `str | null` |

#### `EscalationItemResponse`

| Field | Type |
| --- | --- |
| `id` | `int` |
| `report_id` | `int` |
| `filename` | `str` |
| `description` | `str` |
| `severity` | `str` |
| `source_excerpt` | `str | null` |
| `confidence_score` | `float` |
| `status` | `str` |
| `routing_target` | `str | null` |
| `created_at` | `datetime` |

#### `GovernanceReportResponse`

| Field | Type |
| --- | --- |
| `id` | `int` |
| `document_id` | `int` |
| `filename` | `str` |
| `summary` | `str` |
| `executive_summary` | `str` |
| `confidence_score` | `float` |
| `model_version` | `str` |
| `prompt_version` | `str` |
| `review_status` | `str` |
| `reviewer` | `str | null` |
| `review_notes` | `str | null` |
| `processing_time_seconds` | `float` |
| `tokens_used` | `int` |
| `provider_name` | `str` |
| `version` | `int` |
| `is_latest` | `bool` |
| `created_at` | `datetime` |
| `updated_at` | `datetime` |
| `raid_items` | `RaidItemResponse[]` |
| `escalation_items` | `EscalationItemResponse[]` |

Important gap: `MeetingAction` exists in the database and extraction layer, and some Streamlit UI code expects `meeting_actions`, but `GovernanceReportResponse` currently does not expose `meeting_actions`. The React migration should not assume meeting actions are available from report responses unless the backend API contract is explicitly extended in a separate, compatible change.

#### `DashboardStatsResponse`

| Field | Type |
| --- | --- |
| `total_documents` | `int` |
| `pending_reviews` | `int` |
| `approved_reports` | `int` |
| `failed_jobs` | `int` |
| `total_escalations` | `int` |
| `open_escalations` | `int` |
| `average_confidence` | `float` |
| `average_processing_time` | `float` |
| `total_tokens_consumed` | `int` |
| `reports_generated` | `int` |
| `recent_logs` | `AuditLogResponse[]` |

#### `DashboardChartsResponse`

| Field | Type |
| --- | --- |
| `reports_by_status` | `{label: string, count: number}[]` |
| `escalations_by_severity` | `{label: string, count: number}[]` |
| `raid_distribution` | `{label: string, count: number}[]` |
| `processing_trend` | `{date: string, count: number}[]` |

### Request Schemas

#### `ReportReviewRequest`

| Field | Type | Rule |
| --- | --- | --- |
| `reviewer` | `str` | Required, min length 1 |
| `review_status` | `str` | Must be `approved` or `changes_requested` |
| `review_notes` | `str | null` | Optional |

#### `EscalationRouteRequest`

| Field | Type | Rule |
| --- | --- | --- |
| `routing_target` | `str` | Required, min length 1 |

## Existing Database Schema Inventory

### `users`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer PK | Indexed |
| `username` | String | Unique, indexed, required |
| `role` | String | Required; currently analyst/reviewer semantics |

### `documents`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer PK | Indexed |
| `filename` | String | Required; stored path |
| `type` | String | Required |
| `upload_timestamp` | DateTime | Defaults to UTC now |
| `status` | Enum `WorkflowStatus` | Defaults to `uploaded` |

Relationships:

- `Document.workflow_jobs`
- `Document.reports`

### `workflow_jobs`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer PK | Indexed |
| `document_id` | Integer FK | `documents.id`, cascade delete |
| `status` | Enum `WorkflowStatus` | Defaults to `uploaded` |
| `logs` | Text | Required, default empty string |
| `updated_at` | DateTime | Defaults/updates to UTC now |

### `governance_reports`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer PK | Indexed |
| `document_id` | Integer FK | `documents.id`, cascade delete |
| `summary` | Text | Required |
| `executive_summary` | Text | Required |
| `confidence_score` | Float | Required, default `1.0` |
| `model_version` | String | Required, default `unknown` |
| `prompt_version` | String | Required, default `v1` |
| `document_type` | String | Nullable |
| `classification_confidence` | Float | Nullable |
| `governance_relevance` | String | Nullable |
| `review_status` | String | Required, default `pending_review` |
| `reviewer` | String | Nullable |
| `review_notes` | Text | Nullable |
| `processing_time_seconds` | Float | Required, default `0.0` |
| `tokens_used` | Integer | Required, default `0` |
| `provider_name` | String | Required, default `unknown` |
| `version` | Integer | Required, default `1` |
| `is_latest` | Boolean | Required, default `true` |
| `created_at` | DateTime | Defaults to UTC now |
| `updated_at` | DateTime | Defaults/updates to UTC now |

Relationships:

- `GovernanceReport.document`
- `GovernanceReport.raid_items`
- `GovernanceReport.escalation_items`
- `GovernanceReport.meeting_actions`

### `raid_items`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer PK | Indexed |
| `report_id` | Integer FK | `governance_reports.id`, cascade delete |
| `type` | String | risk/action/issue/dependency |
| `description` | Text | Required |
| `severity` | String | low/medium/high/critical |
| `confidence_score` | Float | Required, default `1.0` |
| `source_excerpt` | Text | Nullable |
| `created_at` | DateTime | Defaults to UTC now |

### `escalation_items`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer PK | Indexed |
| `report_id` | Integer FK | `governance_reports.id`, cascade delete |
| `description` | Text | Required |
| `severity` | String | Required |
| `status` | String | Required, default `open` |
| `routing_target` | String | Nullable |
| `source_excerpt` | Text | Nullable |
| `confidence_score` | Float | Required, default `1.0` |
| `created_at` | DateTime | Defaults to UTC now |

### `meeting_actions`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer PK | Indexed |
| `report_id` | Integer FK | `governance_reports.id`, cascade delete |
| `owner` | String | Required |
| `task` | Text | Required |
| `due_date` | String | Nullable |
| `created_at` | DateTime | Defaults to UTC now |

### `audit_logs`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | Integer PK | Indexed |
| `document_id` | Integer | Nullable, no FK in current model |
| `governance_report_id` | Integer | Nullable, no FK in current model |
| `event` | String | Required |
| `user` | String | Required |
| `details` | Text | Nullable |
| `timestamp` | DateTime | Defaults to UTC now |

## Existing Streamlit Page Inventory

### `frontend/app.py`

Purpose:

- Main landing page.
- Global Streamlit page config.
- Global visual theme CSS.
- Sidebar branding.
- Sidebar role selector.
- Backend display.
- Navigation overview cards for dashboard, upload, workflow, reports, review, and escalations.

React equivalent:

- `AppShell`
- `Sidebar`
- `RoleSwitcher`
- `HomePage`
- `BackendStatusBadge`

### `frontend/pages/1_Dashboard.py`

Purpose:

- Fetch dashboard stats.
- Display KPI cards.
- Display average confidence visual.
- Display recent audit log table.
- Refresh action.

Backend calls:

- `GET /api/governance/dashboard/stats`

React route:

- `/dashboard`

### `frontend/pages/2_Upload_Center.py`

Purpose:

- File upload.
- Client-side document type/complexity heuristics.
- Auto chunk settings.
- Advanced chunk override.
- RAG toggle.
- POST upload with multipart file.
- Upload confirmation and navigation hints.

Backend calls:

- `POST /api/upload?chunk_size=&chunk_overlap=&use_rag=`

React route:

- `/upload`

### `frontend/pages/3_Workflow_Tracker.py`

Purpose:

- Displays recent reports as workflow-like jobs.
- Lets user select a report.
- Fetches report detail.
- Shows approximate pipeline progress.
- Shows executive summary, detailed summary, RAID items, escalations, and processing metrics.

Backend calls:

- `GET /api/governance/reports?is_latest=true`
- `GET /api/governance/reports/{id}`

React route:

- `/workflow`
- Optional detail route: `/workflow/reports/:reportId`

### `frontend/pages/4_Governance_Reports.py`

Purpose:

- Report list.
- Latest-version filter.
- Review-status filter.
- Report expanders.
- Confidence and status badges.
- Executive and detailed summaries.
- Processing metrics.
- Extraction quality metrics.
- RAID summary.
- Risk heatmap.
- Action ownership table if `meeting_actions` appears in response.
- RAID and escalation rationale explainability.

Backend calls:

- `GET /api/governance/reports?is_latest=&review_status=`

React route:

- `/reports`
- Optional detail route: `/reports/:reportId`

### `frontend/pages/5_Review_Queue.py`

Purpose:

- Lists pending review reports.
- Shows summary, RAID, escalation, and metrics tabs.
- Reviewer name field.
- Review notes field.
- Approve or request changes.

Backend calls:

- `GET /api/governance/reports?is_latest=true&review_status=pending_review`
- `PATCH /api/governance/reports/{id}/review`

React route:

- `/review`

### `frontend/pages/6_Escalations.py`

Purpose:

- Escalation list.
- Status filter.
- Summary metrics.
- Open/routed state.
- Route open escalation to target stakeholder.

Backend calls:

- `GET /api/governance/escalations?status=`
- `POST /api/governance/escalations/{id}/route`

React route:

- `/escalations`

## Streamlit to React Route Mapping

| Streamlit Page | React Route | Primary React Page Component |
| --- | --- | --- |
| `frontend/app.py` | `/` | `HomePage` |
| `1_Dashboard.py` | `/dashboard` | `DashboardPage` |
| `2_Upload_Center.py` | `/upload` | `UploadPage` |
| `3_Workflow_Tracker.py` | `/workflow` | `WorkflowPage` |
| selected workflow detail | `/workflow/reports/:reportId` | `WorkflowReportDetailPage` |
| `4_Governance_Reports.py` | `/reports` | `ReportsPage` |
| report detail | `/reports/:reportId` | `ReportDetailPage` |
| `5_Review_Queue.py` | `/review` | `ReviewQueuePage` |
| `6_Escalations.py` | `/escalations` | `EscalationsPage` |

## Recommended React Component Hierarchy

```text
src/
├── app/
│   ├── App.tsx
│   ├── router.tsx
│   └── providers.tsx
├── components/
│   ├── layout/
│   │   ├── AppShell.tsx
│   │   ├── Sidebar.tsx
│   │   ├── TopBar.tsx
│   │   └── PageHeader.tsx
│   ├── ui/
│   │   └── shadcn components
│   ├── feedback/
│   │   ├── LoadingState.tsx
│   │   ├── EmptyState.tsx
│   │   └── ApiErrorAlert.tsx
│   ├── metrics/
│   │   ├── MetricCard.tsx
│   │   ├── ConfidenceBadge.tsx
│   │   ├── StatusBadge.tsx
│   │   └── SeverityBadge.tsx
│   └── governance/
│       ├── RaidItemCard.tsx
│       ├── EscalationCard.tsx
│       ├── AuditLogTable.tsx
│       ├── ProcessingMetrics.tsx
│       └── ExtractionRationale.tsx
├── features/
│   ├── dashboard/
│   │   ├── DashboardPage.tsx
│   │   ├── DashboardKpis.tsx
│   │   └── DashboardCharts.tsx
│   ├── upload/
│   │   ├── UploadPage.tsx
│   │   ├── UploadDropzone.tsx
│   │   ├── ProcessingConfigPanel.tsx
│   │   └── UploadResultCard.tsx
│   ├── workflow/
│   │   ├── WorkflowPage.tsx
│   │   ├── WorkflowTable.tsx
│   │   ├── WorkflowProgress.tsx
│   │   └── WorkflowReportDetail.tsx
│   ├── reports/
│   │   ├── ReportsPage.tsx
│   │   ├── ReportFilters.tsx
│   │   ├── ReportCard.tsx
│   │   ├── ReportDetailPage.tsx
│   │   ├── RaidSummaryTable.tsx
│   │   └── RiskHeatmap.tsx
│   ├── review/
│   │   ├── ReviewQueuePage.tsx
│   │   ├── ReviewReportCard.tsx
│   │   └── ReviewForm.tsx
│   └── escalations/
│       ├── EscalationsPage.tsx
│       ├── EscalationFilters.tsx
│       ├── EscalationSummary.tsx
│       └── RouteEscalationDialog.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts
│   │   ├── endpoints.ts
│   │   └── queryKeys.ts
│   ├── config.ts
│   └── formatters.ts
└── types/
    ├── api.ts
    └── governance.ts
```

## Recommended React State Management Approach

### Server State

Use TanStack Query for all backend data:

- Dashboard stats
- Dashboard charts
- Report list
- Report detail
- Pending review list
- Escalation list
- Workflow job detail

Benefits:

- Loading/error states.
- Request deduplication.
- Refetch after mutations.
- Cache invalidation after review approval or escalation routing.

### Local UI State

Use component state or reducer state for:

- Report filters.
- Escalation filters.
- Upload form values.
- Advanced settings open/closed.
- Selected role.
- Dialog open/closed states.

### Global Client State

Use a small context or Zustand store only for:

- Active user role.
- Sidebar collapse state.
- Optional app-level backend status.

Avoid Redux unless requirements expand significantly.

### Mutations

Use TanStack Query mutations for:

- Upload document.
- Submit report review.
- Route escalation.

After successful mutations:

- Invalidate report queries.
- Invalidate dashboard stats.
- Invalidate escalation queries.
- Optionally navigate to report/workflow detail.

## API Contracts That Must Remain Unchanged

The React migration must not change:

1. `POST /api/upload`
   - Multipart field name must remain `file`.
   - Query params must remain `chunk_size`, `chunk_overlap`, `use_rag`.
   - Response must remain `DocumentResponse`.

2. `GET /api/governance/reports`
   - Query params must remain `is_latest` and `review_status`.
   - Response must remain `GovernanceReportResponse[]`.

3. `GET /api/governance/reports/{id}`
   - Response must remain `GovernanceReportResponse`.

4. `PATCH /api/governance/reports/{id}/review`
   - Payload must remain `{reviewer, review_status, review_notes}`.
   - `review_status` must remain `approved | changes_requested`.

5. `GET /api/governance/dashboard/stats`
   - Response field names must remain stable.

6. `GET /api/governance/dashboard/charts`
   - Response field names must remain stable.

7. `GET /api/governance/escalations`
   - Query param `status` must remain optional.

8. `POST /api/governance/escalations/{id}/route`
   - Payload must remain `{routing_target}`.

9. `GET /health`
   - Must remain available for deployment health checks.

## API Contract Gaps to Track Separately

These are not blockers for migration, but they should be recorded:

1. `meeting_actions` is present in `models.py` but absent from `GovernanceReportResponse`.
2. `document_type`, `classification_confidence`, and `governance_relevance` are present in `GovernanceReport` but absent from `GovernanceReportResponse`.
3. Upload endpoint backend validation allows `pdf`, `docx`, `txt`, and `doc`, while ingestion supports XLSX elsewhere. If React supports XLSX upload, backend upload validation must be extended in a separate backend-compatible change.
4. Current workflow tracker approximates workflow state from reports rather than using `GET /api/workflow/jobs/{id}` in a full job-list workflow.

## Migration Risks and Dependencies

### Backend Contract Risks

- React will make API assumptions more explicit than Streamlit. Missing response fields such as `meeting_actions` may become more visible.
- Current CORS is permissive with `allow_origins=["*"]`. This works for early deployment but should become environment-based for production hardening.
- PostgreSQL migration on Railway requires SQLAlchemy engine config changes because current `connect_args={"check_same_thread": False}` is SQLite-specific.

### File Upload Risks

- Multipart upload must preserve the `file` field name.
- Large file uploads need request timeout handling.
- Upload progress bars require browser-side tracking not present in Streamlit.

### Async Workflow Risks

- Upload returns a `DocumentResponse`, not a workflow job response.
- Background processing is asynchronous, so React needs polling or refresh behavior to find generated reports.
- If richer workflow tracking is desired, backend may need a job-list endpoint later.

### Data Visualization Risks

- Streamlit dataframe behavior must be replaced with explicit table components.
- Risk heatmaps and dashboard charts should use a React chart library such as Recharts.
- Empty states must be carefully designed so a lack of governance items does not look like an application failure.

### Deployment Risks

- Vite frontend env vars are build-time and must use the `VITE_` prefix.
- Railway monorepo deployment should configure service root directories correctly.
- Backend and frontend should be separate Railway services.
- Railway PostgreSQL `DATABASE_URL` must be passed only to the backend service.

### UX Parity Risks

- Streamlit handles reruns automatically; React needs explicit cache invalidation, route navigation, and mutation success handling.
- Streamlit sidebar role state must be reimplemented as context/local storage.
- Existing executive styling should be translated into a consistent Tailwind/shadcn design system.

## Recommended Migration Sequence

1. Preserve current Streamlit frontend during migration.
2. Add React app in a temporary `frontend-react/` or replace `frontend/` only after review.
3. Generate TypeScript API types from FastAPI OpenAPI schema or manually model the current schemas.
4. Build `apiClient`, query keys, and API service functions.
5. Implement `AppShell`, navigation, and empty/loading/error states.
6. Implement Dashboard.
7. Implement Upload Center.
8. Implement Reports list/detail.
9. Implement Review Queue.
10. Implement Escalation Management.
11. Implement Workflow Tracker.
12. Add Dockerfile and Railway frontend config.
13. Add PostgreSQL-safe backend deployment changes.
14. Run `pytest tests/ -v`.
15. Run `python scripts/regression/run_regression_tests.py`.
16. Deploy backend, PostgreSQL, and frontend as Railway services.

## Acceptance Criteria for React Migration

- Existing backend tests pass.
- Existing regression suite remains unchanged.
- No AI extraction, OCR, ontology, or workflow orchestration rewrite.
- All current Streamlit workflows have React equivalents.
- React frontend uses a single centralized API base URL.
- Frontend can run locally against `http://localhost:8000`.
- Frontend can run on Railway against the deployed backend URL.
- API contracts listed above remain stable.

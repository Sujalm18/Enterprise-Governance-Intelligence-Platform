# Known Limitations — Enterprise Governance Intelligence Platform

This document details the simulated architectures, boundaries, and limitations of the platform at the `v1.0.0-rc1` release candidate freeze. These boundaries are addressed in the planned Phase 7 roadmap.

---

## 1. Authentication & Single Sign-On (SSO)
- **Current State**: User authentication is simulated. There is no password verification, JWT validation, or OAuth/SSO login page.
- **Impact**: Anyone visiting the URL has access to the application.
- **Phase 7 Mitigation**: OAuth2.0 andSAM 2.0 (Okta, Entra ID) authentication will be introduced.

---

## 2. Role-Based Access Control (RBAC)
- **Current State**: RBAC permissions are simulated using an active role dropdown in the sidebar which passes user role metadata via headers (`X-User-Role`).
- **Impact**: Role validation is performed client-side and via mock API headers, lacking cryptographically secure token claims enforcement.
- **Phase 7 Mitigation**: Strict route-level JWT scope checks will lock endpoints.

---

## 3. Database Layer (SQLite)
- **Current State**: The application uses a local SQLite file (`data/governance.db`) to store all multi-tenant organization tables.
- **Impact**: SQLite lacks high concurrency write scaling and database clustering support required for multi-tenant SaaS production deployment.
- **Phase 7 Mitigation**: Database migration scripts will migrate schemas to PostgreSQL 16.

---

## 4. Background Workers & Job Queues
- **Current State**: Ingestion parsing and AI extraction pipelines run in-process using Python's asyncio tasks on the API server.
- **Impact**: Massive concurrent document uploads can block API threads, causing performance latency or server timeouts.
- **Phase 7 Mitigation**: Job processing will be decoupled using Celery or Redis Task Queues.

---

## 5. Webhook Alerting Broker
- **Current State**: Slack and MS Teams webhooks are invoked synchronously on state transitions.
- **Impact**: Slow external network requests to Slack/Teams servers will delay API response times.
- **Phase 7 Mitigation**: Webhook dispatch operations will be queued as asynchronous background tasks.

---

## 6. Observability and Monitoring
- **Current State**: Logging is written directly to standard output (`stdout`) and local files, with no centralized APM dashboard.
- **Impact**: There are no proactive alerts for API errors, performance latency spikes, or security anomalies.
- **Phase 7 Mitigation**: Prometheus, OpenTelemetry, and Grafana monitoring stacks will be integrated.

---

## 7. Evaluation Corpus & Test Coverage
- **Current State**: The platform transitioned from basic simulated unit testing to running a comprehensive 90-document evaluation corpus (`data/regression/corpus`) covering multiple formats (PDFs, scanned PDFs with OCR fallback, DOCX, TXT, XLSX).
- **Impact**: Extraction and classification models are verified against realistic, multi-format enterprise governance documents, achieving a 100% pass rate under regression testing.
- **Next Steps**: Continuously expand the corpus with edge-case documents and update expected ground truth annotations to prevent regression as the LLM prompt templates evolve.

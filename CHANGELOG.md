# Changelog — Enterprise Governance Intelligence Platform

All notable changes to the Enterprise Governance Intelligence Platform are documented in this file.

---

## [v1.0.0-rc1] — 2026-06-12 (Phase 1–6 Freeze Release Candidate)
### Added
- **Executive Hub Dashboard**: Multi-dimensional dashboard with Health Score breakdowns, Maturity card matrices, and interactive Priorities cards.
- **Role-Aware AI Copilot**: Context-injected LLM chat helper utilizing the backend's Executive Intelligence Services context.
- **Board Pack Print Styling**: Print preview overlays and `@media print` rules hiding UI controls to export PDF.
- **Chronological snapshots**: Seeded 30-day timelines of historical snapshot values to render charts.
- **Comprehensive Unit Testing**: Added 5 new backend integration/unit tests for intelligence endpoints.
- **Polished Documentation**: Overhauled system design designs, domain model layout, and release guides.

---

## [v0.5.0] — 2026-05-25 (Phase 5)
### Added
- **Multi-Tenant Scopes**: Implemented Organization structures and header interceptors ensuring data isolation.
- **Spreadsheet Exports**: Excel (`openpyxl`) and CSV risk register export downloads.
- **Webhook Alerts**: Slack and MS Teams webhook targets for real-time notification alerts.

---

## [v0.4.0] — 2026-04-10 (Phase 4)
### Added
- **Operations Cockpit**: Interactive queues (Reviews, Escalations, Mitigations, Verifications) and role switcher.
- **Alert Center**: Time-based and event-driven notifications for tasks due soon or overdue.
- **Pipeline Visualizer**: Flow diagram route highlighting pipeline architecture components.

---

## [v0.3.0] — 2026-02-18 (Phase 3)
### Added
- **Mitigation Tasks**: Remediation models with target dates, progress trackers, and ownership assignments.
- **Residual Risk Calculator**: verified completions dynamically scale down original risk score (capped at a 20% floor).
- **Governance Health Score**: Formula deducting points for open risks, escalations, and overdue tasks.

---

## [v0.2.0] — 2025-12-05 (Phase 2)
### Added
- **Playbook Matcher**: Rules-based keyword matcher mapping risk details to mitigations and owners.
- **Risk Score calculations**: Numeric severity weights and confidence mapping.
- **Explainability Trace**: JSON logging explaining Playbook matching decisions.

---

## [v0.1.0] — 2025-10-15 (Phase 1)
### Added
- **Workflow Ingestion**: Multipart upload, text parser, and scanned PDF OCR fallback handlers.
- **Review Queues**: Status progression controls.
- **Audit Logs**: Chronological log record of all platform operations.

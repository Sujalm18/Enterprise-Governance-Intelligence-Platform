# Phase 7 Architecture Design — Production Readiness

This document outlines the planned technical design, configurations, and architecture components for **Phase 7 — Production Readiness**. No Phase 7 code is implemented in the frozen `v1.0.0-rc1` release candidate.

---

## 1. Authentication & Single Sign-On (SSO)
- **Objective**: Replace simulated login credentials and roles with secure, enterprise-grade authentication.
- **Planned Stack**:
  - **SSO Protocol**: OAuth2.0 / SAML 2.0.
  - **Identity Providers (IdP)**: Okta, Azure Active Directory (Microsoft Entra ID), or Keycloak.
  - **Integration**: FastAPI JWT (JSON Web Tokens) Bearer token verification. Token metadata will securely carry user identity and organization keys.

---

## 2. Role-Based Access Control (RBAC)
- **Objective**: Transition from role-simulation headers to cryptographically signed scopes and permissions.
- **Planned Layout**:
  - **Roles**:
    - `Analyst`: Upload compliance documents, view reports, progress mitigation sliders.
    - `Manager`: Approve reports, changes requests, assign owners.
    - `Governance Lead`: Route escalations, close/resolve disputes, verify completed mitigations.
    - `Executive`: Access the Executive Hub dashboard, export reports, and use the Copilot.
  - **Enforcement**: FastAPI dependency security decorators verifying token scopes on route hits (e.g., `@requires_scope("governance:verify")`).

---

## 3. Database Migration: SQLite to PostgreSQL
- **Objective**: Replace SQLite with a robust, concurrent relational database.
- **Planned Layout**:
  - **Database**: PostgreSQL 16.
  - **Connection Pooler**: `PgBouncer` to manage high volumes of database requests.
  - **Migrations**: Integrate `Alembic` inside the backend directory to manage version-controlled table structures and indexes.

---

## 4. Containerization & Orchestration (Docker)
- **Objective**: Standardize environments for local development and cloud packaging.
- **Planned Layout**:
  - **Development Docker Compose**: Sets up backend container, frontend Vite server, PostgreSQL database, and Redis cache.
  - **Production Dockerfile**: Multi-stage builds creating optimized Node.js static bundles served via Nginx and lightweight Python Alpine API runners.

---

## 5. Continuous Integration & Continuous Delivery (CI/CD)
- **Objective**: Automate test execution, linting, image generation, and hosting updates.
- **Planned Setup**:
  - **Tool**: GitHub Actions.
  - **Workflows**:
    - *Lint & Test*: Runs flake8, black, pytest, and frontend typecheck on pull requests to `main`.
    - *Build & Push*: Generates Docker images and pushes to AWS ECR or Docker Hub on release tags.
    - *Deploy*: Triggers CD pipelines to deploy updated instances.

---

## 6. Enterprise Observability & Monitoring
- **Objective**: Track operational health, endpoint latency, API errors, and audit counts.
- **Planned Stack**:
  - **APM**: OpenTelemetry instrumentation exposing metrics to Prometheus and dashboards in Grafana.
  - **Logs Consolidation**: Elasticsearch + Fluentd + Kibana (EFK) or Grafana Loki to query API errors and audit logs.
  - **Alerting**: Sentry for uncaught exception tracking and PagerDuty routing.

---

## 7. Security Hardening
- **Objective**: Mitigate vulnerabilities and comply with SOC2/ISO27001 requirements.
- **Planned Actions**:
  - **CORS Config**: Lock down API Cross-Origin Resource Sharing rules to specific allowed origins.
  - **Rate Limiting**: Integrate `Slowapi` or Redis-based rate limiters to block brute-force attempts on public API endpoints.
  - **Secrets Management**: Replace `.env` configurations with AWS Secrets Manager or HashiCorp Vault.

# Contributing Guidelines — Enterprise Governance Intelligence Platform

Thank you for contributing to the Enterprise Governance Intelligence Platform. This guide outlines setup procedures, coding standards, branch strategies, and code submission processes.

---

## 1. Setup & Environment
The platform requires **Python 3.14+** and **Node.js 20+**.

### Backend Setup
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies and run migrations
pip install -r requirements.txt
python -m backend.app.migrations
```

### Frontend Setup
```powershell
# Navigate and install dependencies
cd frontend
npm install

# Start local Vite development server
npm run dev
```

---

## 2. Branching Strategy
We enforce a strict branch isolation model to preserve stability:
- **`main`**: Protected branch. Contains the stable, frozen Phase 1–6 baseline (`v1.0.0-rc1`). Direct commits are forbidden.
- **`phase7-production-readiness`**: The integration branch for all production readiness upgrades (Authentication, PostgreSQL migration, observability, containerization).
- **Feature Branches**: Created for specific tasks. Merge targets must be set to `phase7-production-readiness` via Pull Requests.

---

## 3. Coding Standards
- **Python**: Follow PEP 8 style formatting.
- **TypeScript & React**: Follow strict type definitions, component modularity, and use Tanstack React Query hooks for asynchronous backend calls.
- **Aesthetics & Design**: Keep UI aligned with premium dashboards (sleek dark mode, glassmorphism, responsive SVG charts, and professional footer print layouts).

---

## 4. Testing Requirements
Before submitting any changes, confirm the validation checks pass successfully:
- **Backend Tests**: Run `python -m pytest` from the workspace root. All tests must pass.
- **Frontend Typecheck**: Run `npm run typecheck` from the `frontend/` directory. Zero compilation errors are allowed.
- **Linting & Code Style**: Confirm your IDE formatting matches repository patterns.

---

## 5. Pull Request (PR) Process
1. Create a feature branch off `phase7-production-readiness`.
2. Commit changes with clear, descriptive commit messages.
3. Push the branch and open a Pull Request targeting `phase7-production-readiness`.
4. Fill in the PR description detailing the problem solved and modifications performed.
5. Confirm that CI/CD runs successfully and request code review from team maintainers.

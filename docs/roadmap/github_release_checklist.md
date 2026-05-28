# GitHub Release Checklist

Follow this checklist before tagging and pushing a new release to GitHub.

## 1. Code Quality & Formatting
- [ ] Run code linter or code formatting tool if available.
- [ ] Ensure all debug lines, hardcoded passwords, and draft mock variables are cleaned or isolated in test environments.
- [ ] Verify that no `.env` or raw API credentials files have been committed to git history.
- [ ] Verify that all imports are absolute and properly qualified (e.g., `from backend.app.services...`).

## 2. Automated Testing
- [ ] Activate the virtual environment:
  ```powershell
  .venv\Scripts\activate
  ```
- [ ] Execute the test suite and verify that all 11 tests pass with no errors:
  ```powershell
  pytest tests/
  ```
- [ ] Double-check that mock AI generation tests cover schema validations and edge case responses (e.g., empty or corrupted text content).

## 3. Versioning & Package Registry
- [ ] Determine the next semantic version number (e.g., `v1.0.0`) based on the changes (Major/Minor/Patch).
- [ ] Update version info in the following files:
  - `backend/app/main.py` (`version="1.0.0"`)
- [ ] Document changes in the release notes / CHANGELOG.md if present.

## 4. Documentation & Assets
- [ ] Confirm that `README.md` reflects current setup instructions and endpoints.
- [ ] Confirm that `architecture.md` matches the latest data flow.
- [ ] Ensure that `deployment_guide.md` details any new configuration variables.
- [ ] Verify that sample files under `data/sample/` are updated and parse correctly.

## 5. Git Tagging & Publish
- [ ] Commit all changes to the main or release branch:
  ```bash
  git add .
  git commit -m "Release v1.0.0"
  ```
- [ ] Push changes to remote:
  ```bash
  git push origin main
  ```
- [ ] Create a git tag for the release:
  ```bash
  git tag -a v1.0.0 -m "Version 1.0.0 Release"
  git push origin v1.0.0
  ```
- [ ] Draft a new Release on GitHub:
  - Select the tag `v1.0.0`.
  - Provide a title: `v1.0.0 - Enterprise AI Governance & Operations Copilot (MVP)`.
  - Add summary descriptions of features, bug fixes, and setup instructions.
  - Publish the release.

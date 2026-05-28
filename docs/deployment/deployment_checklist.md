# Deployment Checklist

## Preflight

- [ ] `pytest tests/ -v` passes.
- [ ] `python scripts/regression/run_regression_tests.py` completes.
- [ ] `.env` created from `.env.example`.
- [ ] `data/` persistence configured.
- [ ] `/health` endpoint returns `healthy`.
- [ ] Upload directory is writable.
- [ ] OCR dependencies are available in the runtime image.

## Docker

- [ ] `docker compose -f deployment/docker/docker-compose.yml up --build` starts API and frontend.
- [ ] API reachable at `http://localhost:8000/health`.
- [ ] Frontend reachable at `http://localhost:8501`.
- [ ] `data/` volume persists SQLite database and uploads.

## Cloud

- [ ] Backend URL is public and stable.
- [ ] Frontend `API_BASE_URL` points to deployed backend.
- [ ] File upload size limits are configured.
- [ ] Logs are retained.
- [ ] Secrets are stored in platform secret manager.

## Demo Readiness

- [ ] Demo dataset loaded.
- [ ] Dashboard has sample reports.
- [ ] Regression report is up to date.
- [ ] README screenshots/GIFs are captured or placeholders are documented.

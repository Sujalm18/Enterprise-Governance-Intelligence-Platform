# Deployment Checklist

## Preflight

- [ ] `pytest tests/ -v` passes.
- [ ] `python scripts/regression/run_regression_tests.py` completes.
- [ ] `.env` created from `.env.example`.
- [ ] Backend env validates with `python scripts/deployment/validate_env.py backend --env-file .env.example`.
- [ ] Frontend env validates with `python scripts/deployment/validate_env.py frontend --env-file frontend/.env.example`.
- [ ] `data/` persistence configured.
- [ ] `/health` endpoint returns `healthy`.
- [ ] Upload directory is writable.
- [ ] OCR dependencies are available in the runtime image.

## Docker

- [ ] `docker compose -f deployment/docker/docker-compose.yml up --build` starts API and frontend.
- [ ] API reachable at `http://localhost:8000/health`.
- [ ] React frontend reachable at `http://localhost:3000`.
- [ ] `data/` volume persists SQLite database and uploads.

## Railway

- [ ] PostgreSQL service is provisioned.
- [ ] Backend service root is `backend/`.
- [ ] Frontend service root is `frontend/`.
- [ ] Backend `DATABASE_URL` references Railway PostgreSQL.
- [ ] Frontend `VITE_API_BASE_URL` points to deployed backend.
- [ ] Backend `FRONTEND_ORIGIN` points to deployed frontend.
- [ ] Backend `CORS_ORIGINS` includes deployed frontend.
- [ ] Backend health check path is `/health`.
- [ ] Frontend health check path is `/health`.
- [ ] File upload size limits are configured.
- [ ] Logs are retained.
- [ ] Secrets are stored in platform secret manager.

## Demo Readiness

- [ ] Demo dataset loaded.
- [ ] Dashboard has sample reports.
- [ ] Regression report is up to date.
- [ ] README screenshots/GIFs are captured or placeholders are documented.

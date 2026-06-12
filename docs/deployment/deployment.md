# Deployment Guide

## Local Docker

```bash
docker compose -f deployment/docker/docker-compose.yml up --build
```

Services:

- Backend API: `http://localhost:8000`
- React frontend: `http://localhost:3000`

## Environment

Copy `.env.example` to `.env` and adjust settings.

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Railway

Railway is the recommended full-stack deployment target.

Services:

- Backend service rooted at `backend/`
- Frontend service rooted at `frontend/`
- Railway PostgreSQL service

Use:

- [Railway deployment guide](railway_deployment.md)
- [Backend environment example](../../deployment/railway/backend.env.example)
- [Frontend environment example](../../deployment/railway/frontend.env.example)

Health checks:

- Backend: `/health`
- Frontend: `/health`

## Render

Backend:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- Add persistent disk for `data/` if database persistence is required.

Frontend:

- Start command: `npm --prefix frontend run preview` (for serving built assets). For development: `npm --prefix frontend run dev`.
- Set `API_BASE_URL` once frontend configuration is externalized.

## Azure App Service

- Deploy backend as a Python web app or container.
- Configure startup command:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

- Use Azure Files or a managed database for production persistence.

## Frontend Hosting (Railway)

Railway can host the frontend (built with Vite) while the backend runs as a separate Railway service.

Limitations:

- Localhost API calls must be replaced by a public backend URL.
- File upload and database persistence must be handled by the backend service.

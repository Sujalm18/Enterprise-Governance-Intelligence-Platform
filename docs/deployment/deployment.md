# Deployment Guide

## Local Docker

```bash
docker compose -f deployment/docker/docker-compose.yml up --build
```

Services:

- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:8501`

## Environment

Copy `.env.example` to `.env` and adjust settings.

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

## Render

Backend:

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
- Add persistent disk for `data/` if database persistence is required.

Frontend:

- Start command: `streamlit run frontend/app.py --server.port $PORT --server.address 0.0.0.0`
- Set `API_BASE_URL` once frontend configuration is externalized.

## Railway

- Use `deployment/docker/Dockerfile` or a Python service.
- Expose port `8000` for the API.
- Use a volume for `data/`.

## Azure App Service

- Deploy backend as a Python web app or container.
- Configure startup command:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

- Use Azure Files or a managed database for production persistence.

## Streamlit Cloud

Streamlit Cloud can host the frontend demo if the backend is deployed separately.

Limitations:

- Localhost API calls must be replaced by a public backend URL.
- File upload and database persistence must be handled by the backend service.

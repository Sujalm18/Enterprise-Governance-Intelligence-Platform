# Frontend

React, TypeScript, Vite, Tailwind CSS, and shadcn/ui frontend for the Enterprise Governance Intelligence Platform.

The frontend is deployed as a standalone Railway service and communicates with the FastAPI backend through `VITE_API_BASE_URL`.

## Local Development

Prerequisites:

- Node.js 20+
- Backend API running on `http://localhost:8000`

Install and run:

```powershell
npm install
npm run dev
```

The app runs locally at `http://localhost:5173`.

## Environment

Create `frontend/.env` for local overrides:

```env
VITE_API_BASE_URL=http://localhost:8000
```

The default fallback in `src/lib/config.ts` is `http://localhost:8000`.

## Production Build

```powershell
npm run build
```

The production build is emitted to `dist/`.

## Railway Deployment

Railway service settings:

- Root directory: `frontend`
- Build method: Dockerfile
- Dockerfile: `frontend/Dockerfile`
- Health check path: `/health`

Required variable:

```env
VITE_API_BASE_URL=https://your-backend-service.up.railway.app
```

The Dockerfile builds the Vite app and serves it through nginx. nginx listens on Railway's `$PORT` and provides SPA fallback for client-side routing.

## Health Check

```powershell
curl https://your-frontend-service.up.railway.app/health
```

Expected response:

```text
healthy
```

## Legacy Streamlit Files

The repository still contains legacy Streamlit files for historical compatibility:

- `app.py`
- `config.py`
- `pages/`

The Railway frontend deployment uses the React application and ignores legacy Streamlit files through `.dockerignore`.


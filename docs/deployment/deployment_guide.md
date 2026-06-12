# Deployment & Operations Guide

This guide outlines the deployment procedures, environment variables, production configurations, and operational checklists for deploying the Enterprise AI Governance & Operations Copilot.

---

## 1. Environment Configurations

All service settings can be overridden via environment variables or a `.env` file located in the project root folder.

### Configuration Reference:

| Variable Name | Default Value | Description |
|---|---|---|
| `APP_NAME` | `Governance Copilot` | The display name of the application. |
| `DATABASE_URL` | `sqlite:///./data/governance.db` | SQLAlchemy connection string. |
| `UPLOAD_DIR` | `./data/uploads` | Directory where uploaded files are stored. |
| `LOG_LEVEL` | `INFO` | Level of logging output (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `AI_PROVIDER` | `mock` | Selected AI engine (`anthropic` or `mock`). |
| `ANTHROPIC_API_KEY` | `None` | API credential key for Claude integrations. |
| `USE_MOCK_MODE` | `True` (if key missing) | Auto-fallbacks to Mock if Claude credentials are empty. |
| `USE_RAG` | `True` | Flags if retrieval-augmented context injection is enabled. |
| `CHUNK_SIZE` | `1000` | Size of chunks for file parsing in characters. |
| `CHUNK_OVERLAP` | `200` | Overlap size of chunks in characters. |

---

## 2. Production Deployment Steps (Windows OS)

Since this app is designed for internal enterprise deployment on Windows environments without Docker, follow these steps to host it as background services.

### Step A: Prerequisites & Virtual Environment
1. Ensure Python 3.11 or higher is installed and added to the PATH.
2. Initialize and prepare the virtual environment in the project directory:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Step B: Service Configuration (NSSM - Non-Sucking Service Manager)
Use NSSM to register both FastAPI (backend) and the frontend (as a Node/Vite service) as Windows Background Services. Note: legacy Streamlit artifacts are retained for historical reference.

1. **Backend Service Registration**:
   - Download NSSM and run: `nssm install GovCopilotBackend`
   - Configure parameters:
     - **Path**: `C:\Users\10651.PHNTECHNOLOGY\Desktop\Projects\Enterprise AI\.venv\Scripts\python.exe`
     - **Startup directory**: `C:\Users\10651.PHNTECHNOLOGY\Desktop\Projects\Enterprise AI`
     - **Arguments**: `-m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000`
   - Click **Install Service**.

2. **Frontend Service Registration (React)**:
   - Run: `nssm install GovCopilotFrontend`
   - Configure parameters:
     - **Path**: `C:\Program Files\nodejs\npm.cmd` (or your path to npm)
     - **Startup directory**: `C:\Users\10651.PHNTECHNOLOGY\Desktop\Projects\Enterprise AI\frontend`
     - **Arguments**: `run dev` (or `run preview` for built assets)
   - Click **Install Service**.

3. **Start Services**:
   - Start via PowerShell:
     ```powershell
     Start-Service GovCopilotBackend
     Start-Service GovCopilotFrontend
     ```

### Step C: Legacy MVP Interface (Optional)
If you wish to host the original Streamlit prototype:
- Run: `nssm install GovCopilotLegacy`
- **Path**: `C:\Users\10651.PHNTECHNOLOGY\Desktop\Projects\Enterprise AI\.venv\Scripts\python.exe`
- **Arguments**: `-m streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0`

---

## 3. Production Deployment Steps (Linux/Unix OS)

If migrating to Linux, use `systemd` and `Nginx`.

### Systemd Service Configuration (`/etc/systemd/system/gov_backend.service`):
```ini
[Unit]
Description=Enterprise Governance Backend API
After=network.target

[Service]
User=appuser
WorkingDirectory=/home/appuser/enterprise-ai
ExecStart=/home/appuser/enterprise-ai/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Configure a similar systemd file for the React frontend (using a Node server or Vite preview), then run:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gov_backend.service gov_frontend.service
sudo systemctl start gov_backend.service gov_frontend.service
```

*(Note: If you still need the Legacy MVP Interface, you can configure a separate `gov_legacy.service` running Streamlit).*

---

## 4. Security & Hardening

1. **API Security**: 
   - Restrict incoming requests to localhost or an internal corporate firewall.
   - For public-facing setups, configure an SSL reverse proxy (e.g., Nginx, IIS) to handle HTTPS, and add authentication headers.
2. **Directory Permissions**:
   - Limit read/write access to the `data/` and `data/uploads/` directory to the service user executing the applications.
3. **Database Security**:
   - SQLite is stored in `data/governance.db`. Make sure this file is backed up daily.
   - If migrating to a multi-node/concurrent setup, upgrade `DATABASE_URL` to a PostgreSQL engine.

---

## 5. Troubleshooting & Logs

- **Application Logs**: Backend logs are routed to stdout and a rolling file located at `data/logs/governance_copilot.log` as configured in `logging_config.py`.
- **Streamlit Logs**: View execution output using standard Windows Event Viewer (if running under NSSM) or by checking the status tracker.

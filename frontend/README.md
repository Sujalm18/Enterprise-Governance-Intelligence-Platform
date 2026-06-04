# Frontend

Streamlit dashboard for uploading documents, browsing governance reports, reviewing extraction quality, and presenting executive governance insights.

## Architecture

The frontend uses **environment-based API configuration** to support both local development and cloud deployments:

- **API Base URL** is configured via Streamlit secrets with a localhost fallback
- All API requests go through a centralized helper (`make_api_request`) with defensive error handling
- The backend URL is configurable without code changes

### API Configuration Files

- **`config.py`** — Centralized API configuration and request utilities
  - `get_api_base_url()` — Returns API base URL from secrets or localhost fallback
  - `get_api_endpoint(endpoint)` — Constructs full API URLs
  - `make_api_request(method, endpoint, **kwargs)` — Makes API requests with error handling and timeouts
  - `get_backend_display_info()` — Returns backend URL for UI display

### Pages

1. **Dashboard** (`1_Dashboard.py`) — Operational KPIs and audit trail
2. **Upload Center** (`2_Upload_Center.py`) — Document ingestion with configurable parameters
3. **Workflow Tracker** (`3_Workflow_Tracker.py`) — Pipeline monitoring and job details
4. **Governance Reports** (`4_Governance_Reports.py`) — Report browsing and filtering
5. **Review Queue** (`5_Review_Queue.py`) — Review approval/rejection workflow
6. **Escalations** (`6_Escalations.py`) — Escalation routing and management

## Local Development

### Prerequisites
- Python 3.9+
- Streamlit (`pip install streamlit`)
- Backend API running on `http://localhost:8000`

### Run Locally

```powershell
# Install dependencies
pip install -r requirements.txt

# Run frontend
streamlit run frontend/app.py
```

The app will open at `http://localhost:8501` and automatically connect to the local backend.

### Optional: Custom Backend URL

To use a different backend during local development:

1. Create `.streamlit/secrets.toml`:
   ```toml
   API_BASE_URL = "http://localhost:3000"  # Or any other backend URL
   ```

2. Restart the Streamlit app

## Production Deployment

### Prerequisites
- Streamlit Cloud account (https://share.streamlit.io)
- Backend deployed to Render or other hosting
- GitHub repository with this code

### Deploy to Streamlit Cloud

1. **Create `.streamlit/secrets.toml`** in the repo root:
   ```toml
   API_BASE_URL = "https://your-app-name.onrender.com"
   ```

2. **Connect to Streamlit Cloud**:
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your GitHub repo and the `frontend/app.py` file
   - Choose Python version 3.9+

3. **Configure Secrets on Streamlit Cloud**:
   - In your app's settings, go to "Secrets"
   - Copy the content from `.streamlit/secrets.toml.example` and update the API_BASE_URL
   - Example:
     ```toml
     API_BASE_URL = "https://your-render-backend.onrender.com"
     ```

4. **Deploy**:
   - Push to GitHub
   - Streamlit Cloud will automatically redeploy

### Health Check

Verify the frontend is connected to the backend:
- Open the dashboard
- Look for the backend URL in the sidebar under "Backend"
- If you see an error, check that:
  1. The backend is running and accessible
  2. `API_BASE_URL` is set correctly in Streamlit secrets
  3. CORS is enabled on the backend

## API Endpoints

All endpoints are routed through `config.make_api_request()`, which handles:
- Connection errors with user-friendly messages
- Request timeouts
- HTTP error responses
- Network availability checks

### Supported Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/governance/dashboard/stats` | GET | Dashboard KPIs |
| `/api/upload` | POST | Document upload |
| `/api/governance/reports` | GET | List reports |
| `/api/governance/reports/{id}` | GET | Report details |
| `/api/governance/reports/{id}/review` | PATCH | Submit review |
| `/api/governance/escalations` | GET | List escalations |
| `/api/governance/escalations/{id}/route` | POST | Route escalation |

## Timeout & Retry Strategy

### Render Free-Tier Cold Starts

Render's free-tier spins down inactive apps after 15 minutes of inactivity. When the app wakes up, the first request can take **20-60 seconds** to complete. The frontend handles this gracefully:

#### Timeout Configuration

| Request Type | Timeout | Purpose |
|--------------|---------|---------|
| **GET** (reads) | 60s | Includes Render cold-start + automatic retry |
| **POST/PATCH/DELETE** (mutations) | 60-120s | Higher timeout for state changes |
| **Uploads** | 120s | Extra time for large files + cold-start |

#### Automatic Retry Behavior

- **GET requests only** (read-only, idempotent):
  - Auto-retry up to 2 times on timeout/connection error
  - Exponential backoff: 2 seconds, then 5 seconds
  - Example: If first request times out, waits 2s and retries; if that fails, waits 5s and tries once more

- **POST/PATCH/DELETE** (state-changing):
  - Single attempt (no automatic retry to prevent duplicate operations)
  - Uses longer timeout to accommodate cold-start

#### User Experience During Long Requests

1. **First 20 seconds**: Normal loading spinner
2. **After 20 seconds**: "⏳ Backend waking up from Render free-tier sleep. This may take up to 60 seconds on first request. Please wait..."
3. **On timeout with retry**: "⏳ Request timed out. Retrying in 2s... (Attempt 1/2)"
4. **After all retries fail**: Clear message indicating backend is still waking up

#### Local Development

- Requests complete in **<500ms** — timeouts never trigger
- Retry mechanism works but rarely needed
- Use `http://localhost:8000` for instant feedback

#### Production (Render)

- **First request after 15+ min inactivity**: May take 20-60 seconds
- **Subsequent requests**: Fast (<500ms) unless backend is very slow
- **After 15 min inactivity**: Cycle repeats

### Handling Slow Backends

If your backend is consistently slow (>60s on any request):

1. **Check Render logs** for performance issues
2. **Consider upgrading** from Render free-tier to paid plan (always-on service)
3. **Increase timeouts** in `frontend/config.py`:
   ```python
   REQUEST_TIMEOUTS = {
       "GET": 120,      # Increase if needed
       "POST": 120,
       "PATCH": 120,
       "DELETE": 120,
   }
   UPLOAD_TIMEOUT = 180  # Increase if needed
   ```

## Environment Variables

### Local Development

Create `.streamlit/secrets.toml`:
```toml
API_BASE_URL = "http://localhost:8000"
```

### Streamlit Cloud

Set via Streamlit Cloud's Secrets management:
```toml
API_BASE_URL = "https://your-backend.onrender.com"
```

**Note**: The `API_BASE_URL` defaults to `http://localhost:8000` if not set, making local development seamless.

## Testing

### Unit Tests

```powershell
# Run all tests
pytest tests/

# Run frontend-specific tests
pytest tests/ -k frontend
```

### Integration Testing

1. Start the backend API
2. Run the Streamlit app
3. Test each page's functionality

## Troubleshooting

### "Cannot connect to backend"

- Ensure the backend API is running on the configured URL
- Check that `API_BASE_URL` is set correctly
- Verify CORS is enabled on the backend

### Backend URL not found

- Check Streamlit Cloud's "Secrets" tab
- Ensure `API_BASE_URL` matches your Render/hosting URL
- Look for typos in the URL

### Timeout errors

**During first request after Render app spins down (>15 min inactivity):**
- Expected behavior: Request takes 20-60 seconds
- Frontend shows: "⏳ Backend waking up from Render free-tier sleep. Please wait..."
- Solution: Wait for the request to complete (up to 60s), then retry
- The app automatically retries GET requests up to 2 times with backoff

**On subsequent timeout errors:**
- Check [Timeout & Retry Strategy](#timeout--retry-strategy) section
- Check backend performance in Render dashboard logs
- Verify network connectivity
- Consider upgrading to Render paid plan for always-on service

**To debug timeout issues:**
1. Open Render dashboard
2. Check backend service logs for errors
3. Monitor memory/CPU usage
4. Look for application startup errors

## Support

For issues or questions:
1. Check the [main README](../README.md) for deployment instructions
2. Review the [backend README](../backend/README.md) for API details
3. See [Timeout & Retry Strategy](#timeout--retry-strategy) for Render cold-start handling


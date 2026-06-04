"""
Centralized API Configuration for Streamlit Frontend
=====================================================
Provides environment-based API base URL configuration using Streamlit secrets.
Supports both local development (localhost fallback) and production (Render backend).

RENDER FREE-TIER COLD-START HANDLING:
Render's free-tier spins down inactive apps after 15 minutes. When accessed, the
backend takes 20-60 seconds to wake up. This module includes:
  - Increased timeout values (60s for standard requests, 120s for uploads)
  - Cold-start detection (shows message if request takes >20s)
  - Automatic retry with exponential backoff for GET requests
  - User-friendly status messages during long waits

TIMEOUT STRATEGY:
  - GET requests (read-only): 60s timeout, 2x retry
  - POST/PATCH/DELETE (state-changing): Single attempt with higher timeout
  - Uploads (large payloads): 120s timeout for slow networks + cold-start
  - Local development: Requests complete in <500ms, timeouts never trigger
"""

import streamlit as st
import requests
import time
from typing import Optional, Dict, Any
from datetime import datetime


# Timeout configuration for different request types
REQUEST_TIMEOUTS = {
    "GET": 60,          # Standard reads: 60s (includes Render cold-start)
    "POST": 90,         # Mutations: 90s default (can be overridden for uploads)
    "PATCH": 60,        # Updates: 60s
    "DELETE": 60,       # Deletes: 60s
}

UPLOAD_TIMEOUT = 120    # Uploads get longer timeout for large files + cold-start
COLD_START_THRESHOLD = 20  # Show "waking up" message after 20s


def get_api_base_url() -> str:
    """
    Get the API base URL from Streamlit secrets or fall back to localhost.
    
    Returns:
        str: The API base URL (e.g., "http://localhost:8000" or "https://backend.onrender.com")
    """
    return st.secrets.get("API_BASE_URL", "http://localhost:8000")


def get_api_endpoint(endpoint: str) -> str:
    """
    Construct a full API endpoint URL.
    
    Args:
        endpoint: The API endpoint path (e.g., "/governance/reports")
    
    Returns:
        str: The full API URL (e.g., "http://localhost:8000/governance/reports")
    """
    base_url = get_api_base_url()
    # Remove leading slash from endpoint if present to avoid double slashes
    endpoint = endpoint.lstrip("/")
    return f"{base_url}/{endpoint}"


def _should_retry(method: str, exception: Exception) -> bool:
    """
    Determine if a request should be retried.
    
    Only retry GET requests (read-only, idempotent). POST/PATCH/DELETE
    may have side effects, so we don't retry them automatically.
    
    Args:
        method: HTTP method
        exception: The exception that occurred
    
    Returns:
        bool: True if the request should be retried
    """
    if method != "GET":
        return False
    
    # Retry on timeout or connection errors (transient failures)
    return isinstance(
        exception,
        (requests.exceptions.Timeout, requests.exceptions.ConnectionError)
    )


def make_api_request(
    method: str,
    endpoint: str,
    timeout: Optional[int] = None,
    retries: int = 0,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Make an API request with retry logic and cold-start detection.
    
    BEHAVIOR:
    - GET requests: Auto-retry up to 2 times with exponential backoff (2s, 5s)
    - POST/PATCH/DELETE: Single attempt (mutations have side effects)
    - Cold-start detection: Shows "waking up" message if request >20s
    - Timeouts: 60s for reads, 120s for uploads, 90s for other mutations
    
    RENDER COLD-START:
    Render free-tier apps sleep after 15 min inactivity. First request wakes
    the app, taking 20-60 seconds. Subsequent requests are fast.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE, PATCH)
        endpoint: API endpoint path
        timeout: Request timeout in seconds (uses defaults if None)
        retries: Current retry attempt (used internally)
        **kwargs: Additional arguments to pass to requests
    
    Returns:
        Dict: JSON response data if successful, None otherwise
    """
    # Determine timeout based on request type
    if timeout is None:
        # Check if this is an upload (files parameter) for longer timeout
        if "files" in kwargs:
            timeout = UPLOAD_TIMEOUT
        else:
            timeout = REQUEST_TIMEOUTS.get(method, 60)
    
    url = get_api_endpoint(endpoint)
    max_retries = 2 if method == "GET" else 0
    backoff_times = [2, 5]  # Exponential backoff in seconds
    
    # Track request start time for cold-start detection
    start_time = time.time()
    cold_start_message_shown = False
    
    while retries <= max_retries:
        try:
            # Show "waking up" message if request is taking a while
            elapsed = time.time() - start_time
            if elapsed > COLD_START_THRESHOLD and not cold_start_message_shown:
                st.warning(
                    "⏳ **Backend waking up from Render free-tier sleep.** "
                    "This may take up to 60 seconds on first request. Please wait...",
                    icon="⏳"
                )
                cold_start_message_shown = True
            
            response = requests.request(method, url, timeout=timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.Timeout as e:
            elapsed = time.time() - start_time
            
            # For timeouts during Render cold-start, be helpful
            if elapsed > COLD_START_THRESHOLD:
                if retries < max_retries:
                    # Retry after backoff
                    wait_time = backoff_times[retries]
                    st.info(
                        f"⏳ Request timed out. Retrying in {wait_time}s... "
                        f"(Attempt {retries + 1}/{max_retries})",
                        icon="⏳"
                    )
                    time.sleep(wait_time)
                    retries += 1
                    continue
                else:
                    st.error(
                        f"⚠️ Backend at {get_api_base_url()} is still waking up. "
                        f"Request timed out after {int(elapsed)}s. "
                        "Please refresh the page to try again.",
                        icon="😴"
                    )
                    return None
            else:
                # Quick timeout (not Render cold-start)
                st.error(
                    f"⚠️ Request to {get_api_base_url()} timed out after {timeout}s. "
                    "Please try again.",
                    icon="⏱️"
                )
                return None
        
        except requests.exceptions.ConnectionError as e:
            if _should_retry(method, e) and retries < max_retries:
                # Retry after backoff
                wait_time = backoff_times[retries]
                st.warning(
                    f"🔄 Connection lost. Retrying in {wait_time}s... "
                    f"(Attempt {retries + 1}/{max_retries})",
                    icon="🔄"
                )
                time.sleep(wait_time)
                retries += 1
                continue
            else:
                st.error(
                    f"⚠️ Cannot connect to backend at {get_api_base_url()}. "
                    "Is the server running?",
                    icon="🔌"
                )
                return None
        
        except requests.exceptions.HTTPError as e:
            st.error(
                f"❌ API request failed: {e.response.text if e.response else str(e)}",
                icon="❌"
            )
            return None
        
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}", icon="❌")
            return None
    
    return None


def get_backend_display_info() -> str:
    """
    Get backend information for display in the UI.
    
    Returns:
        str: Backend URL for display (truncated if too long)
    """
    url = get_api_base_url()
    # Truncate long URLs for display
    if len(url) > 40:
        return url[:37] + "..."
    return url

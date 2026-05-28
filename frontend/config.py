"""
Centralized API Configuration for Streamlit Frontend
=====================================================
Provides environment-based API base URL configuration using Streamlit secrets.
Supports both local development (localhost fallback) and production (Render backend).
"""

import streamlit as st
import requests
from typing import Optional, Dict, Any


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


def make_api_request(
    method: str,
    endpoint: str,
    timeout: int = 10,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    Make an API request with defensive error handling.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint path
        timeout: Request timeout in seconds
        **kwargs: Additional arguments to pass to requests
    
    Returns:
        Dict: JSON response data if successful, None otherwise
    """
    url = get_api_endpoint(endpoint)
    
    try:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"⚠️ Cannot connect to backend at {get_api_base_url()}. "
            "Is the server running?"
        )
        return None
    except requests.exceptions.Timeout:
        st.error(
            f"⚠️ Request to {get_api_base_url()} timed out after {timeout} seconds. "
            "Please try again."
        )
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ API request failed: {e.response.text if e.response else str(e)}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
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

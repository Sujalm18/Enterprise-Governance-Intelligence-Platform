"""Validate deployment environment variables for Railway services."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from urllib.parse import urlparse


BACKEND_REQUIRED = ("DATABASE_URL", "FRONTEND_ORIGIN", "CORS_ORIGINS")
BACKEND_OPTIONAL = (
    "APP_NAME",
    "DEBUG",
    "LOG_LEVEL",
    "UPLOAD_DIR",
    "CORS_ALLOW_CREDENTIALS",
    "CHUNK_SIZE",
    "CHUNK_OVERLAP",
    "USE_RAG",
    "USE_MOCK_MODE",
    "AI_PROVIDER",
    "ANTHROPIC_API_KEY",
)
FRONTEND_REQUIRED = ("VITE_API_BASE_URL",)
BOOL_KEYS = {"DEBUG", "USE_RAG", "USE_MOCK_MODE", "CORS_ALLOW_CREDENTIALS"}
INT_KEYS = {"CHUNK_SIZE", "CHUNK_OVERLAP"}


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {path}")

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def merged_env(env_file: Path | None) -> dict[str, str]:
    values = dict(os.environ)
    if env_file:
        values.update(load_env_file(env_file))
    return values


def is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_database_url(value: str) -> str | None:
    if value.startswith("${{") and value.endswith("}}"):
        return None
    parsed = urlparse(value)
    if parsed.scheme in {"sqlite", "postgresql", "postgres"}:
        return None
    return "DATABASE_URL must use sqlite, postgresql, or Railway's ${{Postgres.DATABASE_URL}} reference."


def validate_backend(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for key in BACKEND_REQUIRED:
        if not values.get(key):
            errors.append(f"Missing required backend variable: {key}")

    database_url = values.get("DATABASE_URL", "")
    if database_url:
        error = validate_database_url(database_url)
        if error:
            errors.append(error)

    for key in ("FRONTEND_ORIGIN",):
        value = values.get(key, "")
        if value and not is_http_url(value):
            errors.append(f"{key} must be an http(s) URL.")

    cors_origins = values.get("CORS_ORIGINS", "")
    for origin in [item.strip() for item in cors_origins.split(",") if item.strip()]:
        if not is_http_url(origin):
            errors.append(f"CORS_ORIGINS contains a non-http(s) URL: {origin}")

    for key in BOOL_KEYS:
        value = values.get(key)
        if value and value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
            errors.append(f"{key} must be boolean-like.")

    for key in INT_KEYS:
        value = values.get(key)
        if value and not value.isdigit():
            errors.append(f"{key} must be an integer.")

    configured = sorted(key for key in BACKEND_REQUIRED + BACKEND_OPTIONAL if values.get(key))
    print("Backend environment variables configured:")
    for key in configured:
        print(f"  - {key}")
    return errors


def validate_frontend(values: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for key in FRONTEND_REQUIRED:
        if not values.get(key):
            errors.append(f"Missing required frontend variable: {key}")

    api_base_url = values.get("VITE_API_BASE_URL", "")
    if api_base_url and not is_http_url(api_base_url):
        errors.append("VITE_API_BASE_URL must be an http(s) URL.")

    print("Frontend environment variables configured:")
    for key in FRONTEND_REQUIRED:
        if values.get(key):
            print(f"  - {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Railway deployment environment variables.")
    parser.add_argument("service", choices=("backend", "frontend"))
    parser.add_argument("--env-file", type=Path, default=None)
    args = parser.parse_args()

    values = merged_env(args.env_file)
    errors = validate_backend(values) if args.service == "backend" else validate_frontend(values)

    if errors:
        print("\nEnvironment validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nEnvironment validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Centralized configuration for the Sensei Dash frontend.

All values are overridable via environment variables with the ``SENSEI_`` prefix.
"""

from __future__ import annotations

import os


class Settings:
    """Application settings loaded from environment variables with sensible defaults."""

    # ── Backend target ──────────────────────────────────────────────────
    # To switch the UI between local and deployed backends, change
    # CURRENT_ENV below. No shell exports or .env files required.
    ENVIRONMENTS: dict[str, str] = {
        "local":  "http://localhost:8000",
        "lambda": "https://jfx6lqvth7tagftjplkifzn5hq0ilrcd.lambda-url.us-east-1.on.aws",
    }
    CURRENT_ENV: str = "lambda"

    BACKEND_URL: str = ENVIRONMENTS[CURRENT_ENV]

    # ── Dash server ─────────────────────────────────────────────────────
    DASH_PORT: int = int(os.getenv("SENSEI_DASH_PORT", "8051"))
    DASH_HOST: str = os.getenv("SENSEI_DASH_HOST", "0.0.0.0")
    DASH_DEBUG: bool = os.getenv("SENSEI_DASH_DEBUG", "false").lower() == "true"
    URL_BASE_PATHNAME: str = os.getenv("SENSEI_URL_BASE", "/sensei_v2/")

    # ── Authentication ──────────────────────────────────────────────────
    AUTH_ENABLED: bool = os.getenv("SENSEI_AUTH_ENABLED", "false").lower() == "true"

    # ── HTTP client tuning ──────────────────────────────────────────────
    API_TIMEOUT_QUERY: int = int(os.getenv("SENSEI_API_TIMEOUT_QUERY", "120"))
    API_TIMEOUT_EXECUTE: int = int(os.getenv("SENSEI_API_TIMEOUT_EXECUTE", "60"))
    API_TIMEOUT_INGEST: int = int(os.getenv("SENSEI_API_TIMEOUT_INGEST", "180"))
    API_TIMEOUT_DEFAULT: int = int(os.getenv("SENSEI_API_TIMEOUT_DEFAULT", "30"))
    API_TIMEOUT_HEALTH: int = int(os.getenv("SENSEI_API_TIMEOUT_HEALTH", "5"))
    API_MAX_RETRIES: int = int(os.getenv("SENSEI_API_MAX_RETRIES", "2"))

    # ── Query polling ───────────────────────────────────────────────────
    POLL_INTERVAL_MS: int = int(os.getenv("SENSEI_POLL_INTERVAL_MS", "4000"))

    # ── Cache (diskcache for background query state) ────────────────────
    CACHE_DIR: str = os.getenv("SENSEI_CACHE_DIR", ".cache/sensei_dash")

    # ── Domain display names ────────────────────────────────────────────
    DOMAIN_DISPLAY_NAMES: dict[str, str] = {
        "LM": "Labor Management",
        "WMS": "Warehouse Management",
        "HR": "Human Resources",
    }

    # ── Fallback domains (used when GET /domains is unreachable) ────────
    FALLBACK_DOMAINS: list[str] = ["LM", "WMS", "HR"]


settings = Settings()

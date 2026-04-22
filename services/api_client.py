"""Base HTTP client for communicating with the FastAPI backend.

Features:
- Automatic retry with exponential backoff on transient errors (502/503/504)
- Configurable per-request timeouts
- Structured logging on every request
- Thread-safe (backed by ``requests.Session``)
"""

from __future__ import annotations

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIClient:
    """Thread-safe HTTP client with retry logic and timeout management."""

    def __init__(
        self,
        base_url: str,
        default_timeout: int = 30,
        max_retries: int = 2,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.default_timeout = default_timeout

        self._session = requests.Session()

        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    # ── Core HTTP methods ───────────────────────────────────────────────

    def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Send a GET request and return parsed JSON."""
        url = f"{self.base_url}{path}"
        timeout = timeout or self.default_timeout
        logger.info("GET %s params=%s timeout=%ss", url, params, timeout)
        try:
            resp = self._session.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.error("GET %s timed out after %ss", url, timeout)
            raise
        except requests.exceptions.ConnectionError:
            logger.error("GET %s connection refused", url)
            raise
        except requests.exceptions.HTTPError as exc:
            logger.error("GET %s returned %s", url, exc.response.status_code)
            raise

    def post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Send a POST request and return parsed JSON."""
        url = f"{self.base_url}{path}"
        timeout = timeout or self.default_timeout
        logger.info("POST %s timeout=%ss", url, timeout)
        try:
            resp = self._session.post(url, json=json, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.error("POST %s timed out after %ss", url, timeout)
            raise
        except requests.exceptions.ConnectionError:
            logger.error("POST %s connection refused", url)
            raise
        except requests.exceptions.HTTPError as exc:
            logger.error("POST %s returned %s", url, exc.response.status_code)
            raise

    def put(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Send a PUT request and return parsed JSON."""
        url = f"{self.base_url}{path}"
        timeout = timeout or self.default_timeout
        logger.info("PUT %s params=%s timeout=%ss", url, params, timeout)
        try:
            resp = self._session.put(url, json=json, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.error("PUT %s timed out after %ss", url, timeout)
            raise
        except requests.exceptions.ConnectionError:
            logger.error("PUT %s connection refused", url)
            raise
        except requests.exceptions.HTTPError as exc:
            logger.error("PUT %s returned %s", url, exc.response.status_code)
            raise

    def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Send a DELETE request and return parsed JSON."""
        url = f"{self.base_url}{path}"
        timeout = timeout or self.default_timeout
        logger.info("DELETE %s params=%s timeout=%ss", url, params, timeout)
        try:
            resp = self._session.delete(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.error("DELETE %s timed out after %ss", url, timeout)
            raise
        except requests.exceptions.ConnectionError:
            logger.error("DELETE %s connection refused", url)
            raise
        except requests.exceptions.HTTPError as exc:
            logger.error("DELETE %s returned %s", url, exc.response.status_code)
            raise

    def patch(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict:
        """Send a PATCH request and return parsed JSON."""
        url = f"{self.base_url}{path}"
        timeout = timeout or self.default_timeout
        logger.info("PATCH %s timeout=%ss", url, timeout)
        try:
            resp = self._session.patch(url, json=json, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            logger.error("PATCH %s timed out after %ss", url, timeout)
            raise
        except requests.exceptions.ConnectionError:
            logger.error("PATCH %s connection refused", url)
            raise
        except requests.exceptions.HTTPError as exc:
            logger.error("PATCH %s returned %s", url, exc.response.status_code)
            raise

    # ── Convenience ─────────────────────────────────────────────────────

    def health(self) -> dict:
        """Non-raising health check. Returns status dict or error payload."""
        try:
            return self.get("/health", timeout=5)
        except Exception as exc:
            logger.warning("Health check failed: %s", exc)
            return {"status": "unreachable", "error": str(exc)}

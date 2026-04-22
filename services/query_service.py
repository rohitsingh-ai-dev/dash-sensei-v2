"""Query service — wraps POST /query, POST /execute, GET /domains."""

from __future__ import annotations

import logging
from typing import Any

from services.api_client import APIClient
from config import settings

logger = logging.getLogger(__name__)


class QueryService:
    """Communicate with the query and execution endpoints."""

    def __init__(self, client: APIClient) -> None:
        self._client = client

    def submit_query(
        self,
        question: str,
        source: str | None = None,
        cust: str | None = None,
        whse: str | None = None,
        session_id: str | None = None,
        site_code: str | None = None,
    ) -> dict[str, Any]:
        """POST /query — full NL-to-SQL pipeline. May take 10-60 s."""
        payload: dict[str, Any] = {"question": question}
        if source:
            payload["source"] = source
        if cust:
            payload["cust"] = cust
        if whse:
            payload["whse"] = whse
        if session_id:
            payload["session_id"] = session_id
        if site_code:
            payload["site_code"] = site_code

        return self._client.post(
            "/query", json=payload, timeout=settings.API_TIMEOUT_QUERY
        )

    def execute_sql(
        self,
        sql: str,
        domain: str | None = None,
    ) -> dict[str, Any]:
        """POST /execute — raw SQL execution."""
        payload: dict[str, Any] = {"sql": sql}
        if domain:
            payload["domain"] = domain

        return self._client.post(
            "/execute", json=payload, timeout=settings.API_TIMEOUT_EXECUTE
        )

    def get_customers(self, source: str) -> list[dict]:
        """GET /customers?source=... — returns list of {label, value} dicts."""
        try:
            data = self._client.get(
                "/customers", params={"source": source}, timeout=20
            )
            return data.get("customers", [])
        except Exception:
            logger.warning("GET /customers failed for source=%s", source)
            return []

    def get_warehouses(self, source: str, cust: str) -> dict[str, str]:
        """GET /warehouses?source=...&cust=... — returns {name: id} map."""
        try:
            data = self._client.get(
                "/warehouses", params={"source": source, "cust": cust}, timeout=20
            )
            return data.get("warehouse_map", {})
        except Exception:
            logger.warning("GET /warehouses failed for source=%s cust=%s", source, cust)
            return {}

    def get_domains(self) -> list[str]:
        """GET /domains — returns list of domain keys (e.g. ['HR', 'LM', 'WMS']).

        Falls back to ``settings.FALLBACK_DOMAINS`` on error.
        """
        try:
            data = self._client.get("/domains", timeout=10)
            return data.get("domains", settings.FALLBACK_DOMAINS)
        except Exception:
            logger.warning("GET /domains failed — using fallback domains")
            return list(settings.FALLBACK_DOMAINS)

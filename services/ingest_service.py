"""Ingest service — wraps /ingest endpoints for bulk, selective, browse, update, delete."""

from __future__ import annotations

import logging
from typing import Any

from services.api_client import APIClient
from config import settings

logger = logging.getLogger(__name__)


class IngestService:
    """Communicate with all ingestion endpoints."""

    def __init__(self, client: APIClient) -> None:
        self._client = client

    # ── Bulk ────────────────────────────────────────────────────────────

    def trigger(self) -> dict[str, Any]:
        """POST /ingest — triggers domain config re-ingestion. May take 30-120 s."""
        return self._client.post("/ingest", timeout=settings.API_TIMEOUT_INGEST)

    # ── Selective ingestion ─────────────────────────────────────────────

    def ingest_schema(self, domain: str, elements: list[dict]) -> dict[str, Any]:
        """POST /ingest/schema — upload schema elements for a domain."""
        return self._client.post(
            "/ingest/schema",
            json={"domain": domain, "schema_elements": elements},
            timeout=60,
        )

    def ingest_kpis(self, domain: str, definitions: list[dict]) -> dict[str, Any]:
        """POST /ingest/kpis — upload KPI definitions for a domain."""
        return self._client.post(
            "/ingest/kpis",
            json={"domain": domain, "kpi_definitions": definitions},
            timeout=60,
        )

    def ingest_glossary(self, domain: str, terms: list[dict]) -> dict[str, Any]:
        """POST /ingest/glossary — upload glossary terms for a domain."""
        return self._client.post(
            "/ingest/glossary",
            json={"domain": domain, "glossary_terms": terms},
            timeout=60,
        )

    # ── Fewshots ─────────────────────────────────────────────────────────

    def list_fewshots(self, domain: str) -> dict[str, Any]:
        """GET /ingest/fewshots — list few-shot examples for a domain."""
        return self._client.get("/ingest/fewshots", params={"domain": domain}, timeout=30)

    # ── Browse ──────────────────────────────────────────────────────────

    def list_datapoints(
        self,
        collection: str,
        domain: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """GET /ingest/datapoints — cursor-paginated browse."""
        params: dict[str, Any] = {"collection": collection, "limit": limit}
        if domain:
            params["domain"] = domain
        if cursor:
            params["cursor"] = cursor
        return self._client.get("/ingest/datapoints", params=params, timeout=30)

    # ── Update ──────────────────────────────────────────────────────────

    def update_datapoint(
        self, point_id: str, collection: str, data: dict[str, Any]
    ) -> dict[str, Any]:
        """PUT /ingest/datapoints/{point_id} — update a data point."""
        return self._client.put(
            f"/ingest/datapoints/{point_id}",
            json=data,
            params={"collection": collection},
            timeout=30,
        )

    # ── Delete ──────────────────────────────────────────────────────────

    def delete_datapoint(self, point_id: str, collection: str) -> dict[str, Any]:
        """DELETE /ingest/datapoints/{point_id} — delete a single data point."""
        return self._client.delete(
            f"/ingest/datapoints/{point_id}",
            params={"collection": collection},
        )

    def bulk_delete(self, collection: str, domain: str) -> dict[str, Any]:
        """DELETE /ingest/datapoints — bulk-delete all points for domain + collection."""
        return self._client.delete(
            "/ingest/datapoints",
            params={"collection": collection, "domain": domain},
        )

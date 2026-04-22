"""Report service — wraps full /reports CRUD."""

from __future__ import annotations

import logging
from typing import Any

from services.api_client import APIClient

logger = logging.getLogger(__name__)


class ReportService:
    """Communicate with the reports endpoints."""

    def __init__(self, client: APIClient) -> None:
        self._client = client

    def create(
        self,
        title: str,
        domain: str,
        sql: str,
        cust: str | None = None,
        whse: str | None = None,
        site_code: str | None = None,
        chart_type: str | None = None,
        category_column: str | None = None,
        value_column: str | None = None,
        max_rows: int | None = None,
        chart_title: str | None = None,
    ) -> dict[str, Any]:
        """POST /reports — create and save a report."""
        payload: dict[str, Any] = {
            "title": title,
            "domain": domain,
            "sql": sql,
        }
        optional = {
            "cust": cust,
            "whse": whse,
            "site_code": site_code,
            "chart_type": chart_type,
            "category_column": category_column,
            "value_column": value_column,
            "max_rows": max_rows,
            "chart_title": chart_title,
        }
        for key, val in optional.items():
            if val is not None:
                payload[key] = val

        return self._client.post("/reports", json=payload)

    def list(self, domain: str | None = None) -> dict[str, Any]:
        """GET /reports — list reports, optionally filtered by domain."""
        params = {"domain": domain} if domain else None
        return self._client.get("/reports", params=params, timeout=90)

    def get(self, report_id: str) -> dict[str, Any]:
        """GET /reports/{id} — retrieve single report."""
        return self._client.get(f"/reports/{report_id}")

    def refresh(self, report_id: str) -> dict[str, Any]:
        """POST /reports/{id}/refresh — re-execute stored SQL."""
        return self._client.post(f"/reports/{report_id}/refresh", timeout=120)

    def delete(self, report_id: str) -> dict[str, Any]:
        """DELETE /reports/{id}."""
        return self._client.delete(f"/reports/{report_id}")

    def update(self, report_id: str, **kwargs: Any) -> dict[str, Any]:
        """PATCH /reports/{id} — update chart config or title."""
        payload = {k: v for k, v in kwargs.items() if v is not None}
        return self._client.patch(f"/reports/{report_id}", json=payload)

    def refresh_all(self, domain: str | None = None) -> dict[str, Any]:
        """POST /reports/refresh-all — bulk refresh all reports."""
        params = f"?domain={domain}" if domain else ""
        return self._client.post(f"/reports/refresh-all{params}", timeout=120)

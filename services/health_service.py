"""Health service — wraps GET /health."""

from __future__ import annotations

import logging
from typing import Any

from services.api_client import APIClient

logger = logging.getLogger(__name__)


class HealthService:
    """Communicate with the health endpoint."""

    def __init__(self, client: APIClient) -> None:
        self._client = client

    def check(self) -> dict[str, Any]:
        """GET /health — never raises; returns status dict or error payload."""
        return self._client.health()

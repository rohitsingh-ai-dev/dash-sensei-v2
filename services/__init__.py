"""Service layer — singleton HTTP client instances for the FastAPI backend.

Import individual services directly::

    from services import query_service, report_service
"""

from __future__ import annotations

from config import settings
from services.api_client import APIClient
from services.query_service import QueryService
from services.report_service import ReportService
from services.ingest_service import IngestService
from services.health_service import HealthService

_client = APIClient(
    base_url=settings.BACKEND_URL,
    default_timeout=settings.API_TIMEOUT_DEFAULT,
    max_retries=settings.API_MAX_RETRIES,
)

query_service = QueryService(_client)
report_service = ReportService(_client)
ingest_service = IngestService(_client)
health_service = HealthService(_client)

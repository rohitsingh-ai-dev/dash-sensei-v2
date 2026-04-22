"""SSE stream consumer — runs in a background thread, writes pipeline
steps to diskcache so the Dash polling callback picks them up."""

from __future__ import annotations

import json
import logging

import requests

from config import settings
from utils.cache import set_query_state

logger = logging.getLogger(__name__)


def stream_query(
    query_id: str,
    question: str,
    source: str | None,
    cust: str | None,
    whse: str | None,
    session_id: str | None,
) -> None:
    """Consume POST /query/stream SSE and relay each event to diskcache.

    Designed to be called in a daemon thread from kpi_query.py.
    """
    url = f"{settings.BACKEND_URL}/query/stream"
    payload: dict = {"question": question}
    if source:
        payload["source"] = source
    if cust:
        payload["cust"] = cust
    if whse:
        payload["whse"] = whse
    if session_id:
        payload["session_id"] = session_id

    set_query_state(query_id, 5, "Connecting...", False)

    try:
        with requests.post(
            url, json=payload, stream=True,
            timeout=settings.API_TIMEOUT_QUERY,
        ) as resp:
            resp.raise_for_status()
            event_type: str | None = None

            for line in resp.iter_lines(decode_unicode=True):
                if line is None or line == "":
                    continue

                if line.startswith("event:"):
                    event_type = line[6:].strip()
                elif line.startswith("data:"):
                    data_str = line[5:].strip()
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning("SSE: invalid JSON: %s", data_str[:200])
                        continue

                    if event_type == "status":
                        pct = data.get("pct", 50)
                        msg = data.get("message", "Working...")
                        set_query_state(query_id, pct, msg, False)

                    elif event_type == "result":
                        set_query_state(
                            query_id, 100, "Complete", True,
                            result=data,
                        )

                    elif event_type == "error":
                        set_query_state(
                            query_id, 100,
                            f"Error: {data.get('message', 'Unknown')}",
                            True,
                            error=data.get("message"),
                        )

                    elif event_type == "clarification":
                        set_query_state(
                            query_id, 100, "Clarification needed", True,
                            result={"clarification": data.get("message")},
                        )

                    event_type = None

    except Exception as exc:
        logger.exception("SSE stream failed for query_id=%s", query_id)
        set_query_state(query_id, 100, f"Error: {exc}", True, error=str(exc))

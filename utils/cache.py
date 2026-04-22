"""Diskcache wrapper for background query state management.

Provides a thread-safe, file-backed cache used to communicate between the
background query thread and the Dash polling interval callback.
"""

from __future__ import annotations

import logging
from typing import Any

import diskcache

from config import settings

logger = logging.getLogger(__name__)

# Singleton cache instance — thread-safe and process-safe
cache = diskcache.Cache(settings.CACHE_DIR)

_QUERY_PREFIX = "query_"
_QUERY_TTL = 3600  # 1 hour — auto-cleanup


def set_query_state(
    query_id: str,
    progress: int,
    status: str,
    completed: bool,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    """Write query progress/result into the cache."""
    cache.set(
        f"{_QUERY_PREFIX}{query_id}",
        {
            "progress": progress,
            "status": status,
            "completed": completed,
            "result": result,
            "error": error,
        },
        expire=_QUERY_TTL,
    )


def get_query_state(query_id: str) -> dict[str, Any] | None:
    """Read query progress/result from the cache. Returns ``None`` if missing."""
    return cache.get(f"{_QUERY_PREFIX}{query_id}")

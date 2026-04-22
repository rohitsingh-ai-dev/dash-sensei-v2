"""Sensei Dash Frontend — Entry Point.

Run directly for development::

    python app.py

For production, use waitress or gunicorn::

    waitress-serve --port=8051 app:server
    gunicorn app:server --workers 2 --threads 4 --timeout 120
"""

from __future__ import annotations

import logging
import sys

# ---------------------------------------------------------------------------
# Logging — configure before any other imports
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
from serving import app, server  # noqa: F401, E402
from layout.main_layout import render_main_layout  # noqa: E402

# Register all callbacks by importing the package
import callbacks  # noqa: F401, E402

# Set the application layout
app.layout = render_main_layout()

logger.info("Sensei Dash frontend initialized.")

# ---------------------------------------------------------------------------
# Development server
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from config import settings

    logger.info(
        "Starting Dash dev server on %s:%s (debug=%s)",
        settings.DASH_HOST,
        settings.DASH_PORT,
        settings.DASH_DEBUG,
    )
    app.run(
        host=settings.DASH_HOST,
        port=settings.DASH_PORT,
        debug=settings.DASH_DEBUG,
    )

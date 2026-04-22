"""Dash / Flask application factory.

Creates the Dash app instance with production-grade configuration.
The ``server`` attribute is exposed for WSGI servers (gunicorn / waitress).
"""

from __future__ import annotations

import dash
import dash_bootstrap_components as dbc

from config import settings

app = dash.Dash(
    __name__,
    url_base_pathname=settings.URL_BASE_PATHNAME,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    prevent_initial_callbacks=True,
    title="Sensei",
    update_title="Sensei | Loading...",
)

# Flask instance — used by gunicorn / waitress in production
server = app.server

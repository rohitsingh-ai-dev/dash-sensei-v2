"""Health check callback — display backend connectivity status."""

from __future__ import annotations

import logging

from dash import Input, Output, html

from serving import app
from services import health_service

logger = logging.getLogger(__name__)


@app.callback(
    Output("health_status_badge", "children"),
    Input("tabBarParent", "children"),  # fires when tabs are rendered
    prevent_initial_call=True,
)
def check_health_on_nav(_):
    """Check backend health when user navigates to a tab section."""
    result = health_service.check()
    status = result.get("status", "unknown")

    if status == "healthy":
        color = "#4CAF50"
        text = "Backend: Healthy"
    elif status == "unreachable":
        color = "#f44336"
        text = "Backend: Unreachable"
    else:
        color = "#FF9800"
        text = f"Backend: {status}"

    return html.Span(
        text,
        style={
            "color": "white",
            "backgroundColor": color,
            "padding": "3px 10px",
            "borderRadius": "10px",
            "fontSize": "80%",
        },
    )

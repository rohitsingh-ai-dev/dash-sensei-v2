"""Clientside (JavaScript) callbacks."""

from __future__ import annotations

from dash import Input, Output

from serving import app

# Auto-scroll the KPI output container when content updates
app.clientside_callback(
    """
    function(children) {
        var el = document.getElementById("kpi_output_container");
        if (el) {
            el.scrollTop = el.scrollHeight;
        }
        return null;
    }
    """,
    Output("kpi_output_container", "title"),
    Input("kpi_output_container", "children"),
)

"""Tab bar renderers for the KPI section."""

from __future__ import annotations

from dash import dcc


def render_tabs_kpi() -> dcc.Tabs:
    """Build the tab bar with all available tabs."""
    return dcc.Tabs(
        id="tabs_kpi",
        value="tab_kpi_query",
        children=[
            dcc.Tab(
                label="Ask Sensei",
                value="tab_kpi_query",
                className="custom-tab",
                selected_className="custom-tab--selected",
            ),
            dcc.Tab(
                label="SQL Console",
                value="tab_kpi_runsql",
                className="custom-tab",
                selected_className="custom-tab--selected",
            ),
            dcc.Tab(
                label="Ingestion",
                value="tab_kpi_ingest",
                className="custom-tab",
                selected_className="custom-tab--selected",
            ),
            dcc.Tab(
                label="Reports",
                value="tab_kpi_reports",
                className="custom-tab",
                selected_className="custom-tab--selected",
            ),
        ],
        parent_className="custom-tabs",
        className="custom-tabs-container",
    )

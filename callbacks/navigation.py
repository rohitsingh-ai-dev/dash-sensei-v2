"""Navigation callbacks — breadcrumbs, landing page tiles, tab switching."""

from __future__ import annotations

import logging

from dash import Input, Output, State, ctx, html, no_update

from serving import app
from layout.tabs import render_tabs_kpi
from layout.splash_page import render_splash_page
from layout.kpi_query_tab import render_kpi_query_tab
from layout.run_sql_tab import render_run_sql_tab
from layout.ingestion_tab import render_ingestion_tab
from layout.reports_tab import render_reports_tab

logger = logging.getLogger(__name__)


# ── Landing page tile click → show KPI tabs ─────────────────────────────


@app.callback(
    Output("tabBarParent", "children", allow_duplicate=True),
    Output("splashPageParent", "children", allow_duplicate=True),
    Output("mainTitleBreadcrumbDiv_home", "children", allow_duplicate=True),
    Output("mainTitleBreadcrumbDiv_kpi", "children", allow_duplicate=True),
    Input("selectKPI", "n_clicks"),
    prevent_initial_call=True,
)
def landing_page_kpi_click(n_clicks):
    """User clicked the Davinci Database tile on the landing page."""
    if n_clicks is None or n_clicks == 0:
        return no_update, no_update, no_update, no_update

    logger.info("Landing page: KPI tile clicked")
    return (
        render_tabs_kpi(),
        None,  # Hide splash page
        "Sensei Home",
        "Ask Sensei",
    )


# ── Breadcrumb navigation ───────────────────────────────────────────────


@app.callback(
    Output("tabBarParent", "children", allow_duplicate=True),
    Output("splashPageParent", "children", allow_duplicate=True),
    Output("main_content", "children", allow_duplicate=True),
    Output("mainTitleBreadcrumbDiv_home", "children", allow_duplicate=True),
    Output("mainTitleBreadcrumbDiv_kpi", "children", allow_duplicate=True),
    Input("mainTitleBreadcrumbDiv_home", "n_clicks"),
    Input("mainTitleBreadcrumbDiv_kpi", "n_clicks"),
    prevent_initial_call=True,
)
def go_breadcrumbs(home_clicks, kpi_clicks):
    """Navigate via breadcrumb clicks."""
    triggered = ctx.triggered_id

    if triggered == "mainTitleBreadcrumbDiv_kpi":
        logger.info("Breadcrumb: KPI clicked")
        return (
            render_tabs_kpi(),
            None,
            no_update,
            "Sensei Home",
            "Ask Sensei",
        )

    # Home or unknown — go back to splash
    logger.info("Breadcrumb: Home clicked")
    return (
        None,
        render_splash_page(),
        None,
        "",
        "",
    )


# ── KPI tab switching ───────────────────────────────────────────────────


# Track whether we have already rendered the persistent chat tab
_CHAT_TAB_ID = "cx-persist-tab"
_OTHER_TAB_ID = "other-tab-content"


@app.callback(
    Output("main_content", "children", allow_duplicate=True),
    Output("query_id", "data", allow_duplicate=True),
    Input("tabs_kpi", "value"),
    State("main_content", "children"),
    prevent_initial_call=True,
)
def tabs_kpi_manager(tab_value, current_children):
    """Render tabs — chat tab is rendered once and hidden/shown to preserve state."""
    logger.info("Tab: %s", tab_value)

    # Check if chat tab already exists in current_children
    chat_exists = False
    if isinstance(current_children, list):
        for child in current_children:
            if hasattr(child, "id") and getattr(child, "id", None) == _CHAT_TAB_ID:
                chat_exists = True
                break
            if isinstance(child, dict) and child.get("props", {}).get("id") == _CHAT_TAB_ID:
                chat_exists = True
                break

    show = {"display": "block"}
    hide = {"display": "none"}

    if tab_value == "tab_kpi_query":
        if chat_exists:
            # Show chat, hide other
            return no_update, no_update
        else:
            # First render: create persistent chat tab
            content = [
                html.Div(id=_CHAT_TAB_ID, children=render_kpi_query_tab(), style=show),
            ]
            return content, no_update

    # For all other tabs: render new content
    tab_renderers = {
        "tab_kpi_runsql": render_run_sql_tab,
        "tab_kpi_ingest": render_ingestion_tab,
        "tab_kpi_reports": render_reports_tab,
    }
    renderer = tab_renderers.get(tab_value)
    if renderer is None:
        return None, None

    return renderer(), None


# Show/hide the chat tab based on active tab (client-side for speed)
app.clientside_callback(
    """
    function(tab) {
        var chatEl = document.getElementById('cx-persist-tab');
        if (chatEl) {
            chatEl.style.display = (tab === 'tab_kpi_query') ? 'block' : 'none';
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("main_content", "className", allow_duplicate=True),
    Input("tabs_kpi", "value"),
    prevent_initial_call=True,
)

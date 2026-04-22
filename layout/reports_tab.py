"""Reports tab layout — KPI summary, report grid, create form."""

from __future__ import annotations

import logging

from dash import dcc, html

from config import settings

logger = logging.getLogger(__name__)

_DD_STYLE = {"width": "200px", "backgroundColor": "#1a212a"}

_CHART_TYPE_OPTIONS = [
    {"label": "Bar", "value": "Bar"},
    {"label": "Line", "value": "Line"},
    {"label": "Pie", "value": "Pie"},
    {"label": "Scatter", "value": "Scatter"},
    {"label": "Area", "value": "Area"},
    {"label": "Funnel", "value": "Funnel"},
]


def _load_existing_reports() -> tuple[list, list]:
    """Fetch reports and split into KPI cards + report cards."""
    from callbacks.reports import _build_report_card, _build_kpi_card
    from services import report_service
    from utils.helpers import detect_kpi_indicator

    try:
        data = report_service.list()
        reports = data.get("reports", [])
    except Exception as exc:
        logger.warning("Failed to load reports: %s", exc)
        return [], [html.Div(f"Failed to load reports: {exc}", style={"color": "lightcoral"})]

    if not reports:
        return [], [html.Div("No saved reports yet. Use 'Save to Dashboard' from the chat tab.", className="rpt-empty")]

    kpi_cards = []
    report_cards = []
    for r in reports:
        results = r.get("results") or []
        kpi = detect_kpi_indicator(results)
        if kpi:
            kpi_cards.append(_build_kpi_card(r, kpi))
        report_cards.append(_build_report_card(r))

    if not report_cards:
        report_cards = [html.Div("No reports found.", className="rpt-empty")]

    return kpi_cards, report_cards


def render_reports_tab() -> list:
    """Build the redesigned reports interface."""

    domain_options = [
        {"label": settings.DOMAIN_DISPLAY_NAMES.get(d, d), "value": d.lower()}
        for d in settings.FALLBACK_DOMAINS
    ]

    kpi_cards, report_cards = _load_existing_reports()

    return [
        html.Div(
            children=[
                # ── Section 1: KPI Summary Row ─────────────────────
                html.Div(
                    [
                        html.Div("Key Metrics", className="rpt-heading"),
                        html.Div(
                            children=kpi_cards if kpi_cards else [
                                html.Div("No single-value reports saved yet.", className="rpt-subheading")
                            ],
                            id="reports_kpi_cards_container",
                            className="rpt-kpi-row",
                        ),
                    ],
                    style={"marginBottom": "25px"},
                ),

                # ── Section 2: Filter Bar ──────────────────────────
                html.Div(
                    className="rpt-filter-bar",
                    children=[
                        html.Label("Domain:"),
                        dcc.Dropdown(
                            id="report_list_domain_filter",
                            options=[{"label": "All", "value": ""}] + domain_options,
                            value="",
                            clearable=False,
                            style=_DD_STYLE,
                        ),
                        html.Label("Auto-refresh:", style={"marginLeft": "15px"}),
                        dcc.Dropdown(
                            id="reports_auto_refresh_toggle",
                            options=[
                                {"label": "Off", "value": 0},
                                {"label": "Every 5 min", "value": 300000},
                                {"label": "Every 15 min", "value": 900000},
                                {"label": "Every 30 min", "value": 1800000},
                            ],
                            value=0,
                            clearable=False,
                            style={"width": "160px", "backgroundColor": "#1a212a"},
                        ),
                        html.Button(
                            "Refresh All",
                            id="report_list_refresh_button",
                            n_clicks=0,
                            style={
                                "backgroundColor": "#458e9f",
                                "border": "1px solid gray",
                                "color": "white",
                                "padding": "6px 16px",
                                "borderRadius": "6px",
                                "marginLeft": "10px",
                            },
                        ),
                    ],
                ),

                # Auto-refresh interval (hidden)
                dcc.Interval(
                    id="reports_auto_refresh_interval",
                    interval=300000,
                    n_intervals=0,
                    disabled=True,
                ),

                # ── Section 3: Report Cards Grid ───────────────────
                html.Div("Saved Reports", className="rpt-heading"),
                html.Div(
                    children=report_cards,
                    id="report_list_container",
                    className="rpt-grid",
                ),

                # ── Section 4: Create Report (collapsible) ────────
                html.Details(
                    [
                        html.Summary("Create a New Report"),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dcc.Input(
                                            id="report_title_input",
                                            type="text",
                                            placeholder="Report title (min 3 chars)",
                                            style={"width": "50%", "marginBottom": "10px"},
                                        ),
                                        html.Div(
                                            [
                                                dcc.Dropdown(
                                                    id="report_domain_selector",
                                                    options=domain_options,
                                                    placeholder="Select domain",
                                                    style={"width": "250px", "backgroundColor": "#1a212a"},
                                                ),
                                            ],
                                            style={"marginBottom": "10px"},
                                        ),
                                        dcc.Textarea(
                                            id="report_sql_input",
                                            placeholder="SQL query for this report...",
                                        ),
                                        html.Details(
                                            [
                                                html.Summary("Chart Configuration (optional)"),
                                                html.Div(
                                                    [
                                                        html.Div(
                                                            [
                                                                html.Label("Chart Type:"),
                                                                dcc.Dropdown(
                                                                    id="report_chart_type",
                                                                    options=_CHART_TYPE_OPTIONS,
                                                                    placeholder="Auto-detect",
                                                                    style={"width": "150px", "backgroundColor": "#1a212a"},
                                                                ),
                                                            ],
                                                            style={"marginRight": "15px"},
                                                        ),
                                                        dcc.Input(
                                                            id="report_category_col",
                                                            type="text",
                                                            placeholder="X-axis column",
                                                            style={"marginRight": "10px"},
                                                        ),
                                                        dcc.Input(
                                                            id="report_value_col",
                                                            type="text",
                                                            placeholder="Y-axis column",
                                                            style={"marginRight": "10px"},
                                                        ),
                                                        dcc.Input(
                                                            id="report_chart_title",
                                                            type="text",
                                                            placeholder="Chart title",
                                                        ),
                                                    ],
                                                    style={"display": "flex", "flexWrap": "wrap", "gap": "10px", "marginTop": "10px", "alignItems": "flex-end"},
                                                ),
                                            ],
                                            style={"marginTop": "10px"},
                                        ),
                                        html.Div(
                                            [
                                                html.Button(
                                                    "Save Report",
                                                    id="report_save_button",
                                                    n_clicks=0,
                                                    style={
                                                        "backgroundColor": "#458e9f",
                                                        "border": "1px solid gray",
                                                        "color": "white",
                                                        "padding": "8px 20px",
                                                        "borderRadius": "6px",
                                                        "marginTop": "15px",
                                                    },
                                                ),
                                                html.Div(
                                                    dcc.Loading(
                                                        id="loading-report-create",
                                                        type="dot",
                                                        fullscreen=False,
                                                        color="#388A98",
                                                        children=html.Div(id="loading-output-report-create"),
                                                        className="loader",
                                                        parent_className="loader_parent",
                                                    ),
                                                    style={"display": "inline-block", "marginLeft": "15px", "marginTop": "15px"},
                                                ),
                                            ],
                                        ),
                                        html.Div("", id="report_create_result", style={"color": "white", "fontStyle": "italic", "marginTop": "10px"}),
                                    ],
                                    style={"marginTop": "15px"},
                                ),
                            ],
                        ),
                    ],
                    className="rpt-create-section",
                ),
            ],
            style={"width": "95%", "margin": "0 20px"},
        ),
    ]

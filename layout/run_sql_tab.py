"""Run SQL tab layout — direct SQL execution interface."""

from __future__ import annotations

from dash import dcc, html

from config import settings


def render_run_sql_tab() -> list:
    """Build the raw SQL execution interface."""

    domain_options = [
        {
            "label": settings.DOMAIN_DISPLAY_NAMES.get(d, d),
            "value": d.lower(),
        }
        for d in settings.FALLBACK_DOMAINS
    ]

    return [
        html.Div(
            className="sn-tab-page",
            children=[
                html.Div("SQL Console", className="sn-tab-title"),
                html.Div(
                    "Execute a raw SQL query against the Redshift database.",
                    className="welcome_text",
                ),
                # Domain selector
                html.Div(
                    className="sn-field-row",
                    children=[
                        html.Label("Domain (optional):", className="sn-field-label"),
                        dcc.Dropdown(
                            id="runsql_domain_selector",
                            options=domain_options,
                            placeholder="Select domain",
                            style={"width": "250px"},
                        ),
                    ],
                ),
                # SQL input
                dcc.Textarea(
                    id="runsql_input",
                    placeholder="Enter your SQL query here...",
                    className="sn-textarea",
                    style={"height": "150px", "marginTop": "10px"},
                ),
                # Execute button + loader
                html.Div(
                    className="sn-field-row",
                    style={"marginTop": "10px"},
                    children=[
                        html.Button(
                            "Execute",
                            id="runsql_submit_button",
                            n_clicks=0,
                            className="sn-btn",
                        ),
                        dcc.Loading(
                            id="loading-runsql",
                            type="dot",
                            fullscreen=False,
                            color="#388A98",
                            children=html.Div(id="loading-output-runsql"),
                            className="loader",
                            parent_className="loader_parent",
                        ),
                    ],
                ),
                # Results
                html.Div(
                    children=[],
                    id="runsql_output_container",
                    className="sn-results-area",
                ),
            ],
        ),
    ]

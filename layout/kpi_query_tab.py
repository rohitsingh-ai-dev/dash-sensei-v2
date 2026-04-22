"""KPI query tab — clean ChatGPT-style conversational layout.

Only two fixed elements: filter pills (top) + input bar (bottom).
Everything else (results, SQL, save, errors) lives inside chat bubbles.
"""

from __future__ import annotations

from dash import dcc, html
import dash_bootstrap_components as dbc

from config import settings


def render_kpi_query_tab() -> list:
    domain_options = [
        {"label": settings.DOMAIN_DISPLAY_NAMES.get(d, d), "value": d.lower()}
        for d in settings.FALLBACK_DOMAINS
    ]

    return [
        # ── Hidden elements for callback compatibility ───────────
        html.Div(id="kpi_questions_parent", children=[
            html.Div(id={"type": "kpi_questions", "index": 0}, style={"display": "none"}),
        ], style={"display": "none"}),
        html.Div(id="loading-output-kpi", style={"display": "none"}),
        html.Div(id="kpi_output_container_parent", style={"display": "none"}),
        html.Div(id="kpi_output_container_save", children=[
            dcc.Input(id="kpi_save_name", type="text", style={"display": "none"}),
            html.Button(id="submit_kpi_button_save", n_clicks=0, style={"display": "none"}),
            html.Button(id="submit_kpi_button_cancel", n_clicks=0, style={"display": "none"}),
        ], style={"display": "none"}),
        html.Div(id="welcome_message", style={"display": "none"}),
        html.Div(id="chat_history_list", style={"display": "none"}),
        dbc.Progress(value=0, id="progress_bar", style={"display": "none"}),
        html.Div(id="progress_status", style={"display": "none"}),
        dcc.Store(id="warehouse_id_map", data={}),
        dcc.Store(id="chat_sql_store", data=""),

        # ── THE UI: filter bar + chat + input bar ────────────────
        html.Div(className="cx", children=[

            # ── Filter pills (top bar) ───────────────────────────
            html.Div(className="cx-filters", children=[
                html.Div(dcc.Dropdown(
                    id="source_selector",
                    options=domain_options,
                    placeholder="Select Source",
                    className="cx-dd",
                ), className="cx-filter-wrap"),
                html.Div(dcc.Dropdown(
                    id="cust_input",
                    options=[],
                    placeholder="Select Customer",
                    className="cx-dd",
                    disabled=True,
                ), className="cx-filter-wrap"),
                html.Div(dcc.Dropdown(
                    id="whse_input",
                    options=[],
                    placeholder="Select Warehouse",
                    className="cx-dd",
                    disabled=True,
                ), className="cx-filter-wrap"),
                html.Button("+ New Chat", id="new_chat_btn", n_clicks=0, className="cx-new"),
            ]),

            # ── Chat area (scrollable) ───────────────────────────
            html.Div(id="kpi_output_container", className="cx-chat", children=[
                html.Div(className="cx-spacer"),  # pushes messages to bottom
                html.Div(className="cx-row", children=[
                    html.Div("S", className="cx-av cx-av-s"),
                    html.Div(className="cx-bub cx-bub-s", children=[
                        "Hi! I'm Sensei, your data assistant. ",
                        "Select a source, customer, and warehouse above to get started.",
                    ]),
                ]),
            ]),

            # ── Input bar (bottom) ───────────────────────────────
            html.Div(className="cx-input-bar", children=[
                dcc.Input(
                    id="kpi_input",
                    type="text",
                    placeholder="Ask a question about your data...",
                    className="cx-input",
                    debounce=False,
                ),
                html.Button("Send", id="submit_kpi_button", n_clicks=0, className="cx-send"),
            ]),
        ]),
    ]

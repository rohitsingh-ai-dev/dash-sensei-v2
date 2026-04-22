"""Ingestion tab layout — bulk ingest, selective upload, browse & manage.

Uses shared CSS classes from theme.css for consistent styling.
"""

from __future__ import annotations

from dash import dash_table, dcc, html


# ── Shared constants ──────────────────────────────────────────────────────

_DOMAIN_OPTS = [
    {"label": "LM — Labor Management", "value": "LM"},
    {"label": "WMS — Warehouse Management", "value": "WMS"},
    {"label": "HR — Human Resources", "value": "HR"},
]

_COLL_OPTS = [
    {"label": "Schema Elements", "value": "schema"},
    {"label": "KPI Definitions", "value": "kpi"},
    {"label": "Glossary Terms", "value": "glossary"},
    {"label": "Few-Shot Examples", "value": "fewshots"},
]


# ── Section 1: Bulk Re-Ingest ──────────────────────────────────────────────


def _bulk_ingest_section() -> html.Div:
    return html.Div(
        className="sn-card",
        children=[
            html.Div("Bulk Re-Ingest", className="sn-card-heading"),
            html.Div(
                "Re-ingest all domain config files (schema, KPIs, glossary) into the vector database.",
                className="sn-card-sub",
            ),
            html.Div(
                className="sn-field-row",
                children=[
                    html.Button("Trigger Ingestion", id="ingest_submit_button", n_clicks=0, className="sn-btn"),
                    dcc.Loading(
                        id="loading-ingest",
                        type="dot",
                        fullscreen=False,
                        color="#388A98",
                        children=html.Div(id="loading-output-ingest"),
                        className="loader",
                        parent_className="loader_parent",
                    ),
                ],
            ),
            html.Div(
                id="ingest_output_container",
                className="sn-results-area",
            ),
        ],
    )


# ── Section 2: Selective Upload ────────────────────────────────────────────


def _selective_upload_section() -> html.Div:
    return html.Div(
        className="sn-card",
        children=[
            html.Div("Selective Upload", className="sn-card-heading"),
            html.Div(
                "Upload individual schema elements, KPI definitions, or glossary terms as a JSON array.",
                className="sn-card-sub",
            ),
            # Domain row
            html.Div(
                className="sn-field-row",
                children=[
                    html.Div("Domain", className="sn-field-label"),
                    html.Div(
                        dcc.Dropdown(id="upload_domain", options=_DOMAIN_OPTS, value="LM", clearable=False),
                        style={"width": "280px"},
                    ),
                ],
            ),
            # Type row
            html.Div(
                className="sn-field-row",
                style={"marginBottom": "18px"},
                children=[
                    html.Div("Type", className="sn-field-label"),
                    html.Div(
                        dcc.Dropdown(id="upload_type", options=_COLL_OPTS, value="schema", clearable=False),
                        style={"width": "280px"},
                    ),
                ],
            ),
            # JSON input
            dcc.Textarea(
                id="upload_json_input",
                placeholder=(
                    'Paste a JSON array, e.g.:\n'
                    '[\n'
                    '  {\n'
                    '    "table_name": "lmdata",\n'
                    '    "column_name": "new_col",\n'
                    '    "data_type": "VARCHAR(50)",\n'
                    '    "description": "Description here",\n'
                    '    "usage": "Used for ..."\n'
                    '  }\n'
                    ']'
                ),
                className="sn-textarea",
                style={"height": "160px"},
            ),
            # Upload button
            html.Div(
                className="sn-field-row",
                style={"marginTop": "10px"},
                children=[
                    html.Button("Upload", id="upload_submit_button", n_clicks=0, className="sn-btn"),
                    dcc.Loading(
                        id="loading-upload",
                        type="dot",
                        fullscreen=False,
                        color="#388A98",
                        children=html.Div(id="loading-output-upload"),
                        className="loader",
                        parent_className="loader_parent",
                    ),
                ],
            ),
            html.Div(
                id="upload_output_container",
                className="sn-results-area",
            ),
        ],
    )


# ── Section 3: Browse & Manage ─────────────────────────────────────────────


def _browse_manage_section() -> html.Div:
    return html.Div(
        className="sn-card",
        children=[
            html.Div("Browse & Manage Data Points", className="sn-card-heading"),
            html.Div(
                "View, edit, or delete data points that are currently ingested in the vector database.",
                className="sn-card-sub",
            ),
            # ── Filter rows ──
            html.Div(
                className="sn-field-row",
                children=[
                    html.Div("Collection", className="sn-field-label"),
                    html.Div(
                        dcc.Dropdown(id="browse_collection", options=_COLL_OPTS, value="schema", clearable=False),
                        style={"width": "280px"},
                    ),
                ],
            ),
            html.Div(
                className="sn-field-row",
                children=[
                    html.Div("Domain", className="sn-field-label"),
                    html.Div(
                        dcc.Dropdown(
                            id="browse_domain",
                            options=[{"label": "All Domains", "value": ""}] + _DOMAIN_OPTS,
                            value="",
                            clearable=False,
                        ),
                        style={"width": "280px"},
                    ),
                ],
            ),
            html.Div(
                html.Button("Load Data Points", id="browse_load_button", n_clicks=0, className="sn-btn"),
                style={"marginBottom": "18px"},
            ),
            # ── Count + action bar ──
            html.Div(
                style={"display": "flex", "alignItems": "center", "marginBottom": "10px"},
                children=[
                    html.Div(id="browse_total_count", style={"color": "#aaa", "fontSize": "90%", "flex": "1"}),
                    html.Button("Bulk Delete All", id="browse_bulk_delete_button", n_clicks=0,
                                className="sn-btn-danger", style={"fontSize": "80%", "padding": "5px 14px"}),
                ],
            ),
            # ── Data table (Dash DataTable requires Python style dicts) ──
            dash_table.DataTable(
                id="browse_table",
                columns=[
                    {"name": "Point ID", "id": "point_id"},
                    {"name": "Domain", "id": "domain"},
                ],
                data=[],
                row_selectable="single",
                style_table={"overflowX": "auto", "borderRadius": "8px"},
                style_header={
                    "backgroundColor": "#1a212a",
                    "color": "white",
                    "fontWeight": "bold",
                    "border": "none",
                    "borderBottom": "2px solid #458e9f",
                    "padding": "10px 12px",
                    "fontSize": "90%",
                },
                style_cell={
                    "backgroundColor": "#2a3040",
                    "color": "#ddd",
                    "border": "none",
                    "borderBottom": "1px solid #3a4050",
                    "textAlign": "left",
                    "padding": "10px 12px",
                    "maxWidth": "350px",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "fontSize": "85%",
                },
                style_cell_conditional=[
                    {"if": {"column_id": "point_id"}, "width": "22%", "fontFamily": "monospace", "fontSize": "80%"},
                    {"if": {"column_id": "domain"}, "width": "10%"},
                ],
                style_data_conditional=[
                    {
                        "if": {"state": "selected"},
                        "backgroundColor": "#3a4a5a",
                        "border": "none",
                        "borderBottom": "1px solid #458e9f",
                    },
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "#252d3a",
                    },
                ],
                page_size=15,
            ),
            # ── Stores ──
            dcc.Store(id="browse_cursor_store", data=None),
            dcc.Store(id="browse_data_store", data=[]),
            dcc.Store(id="browse_reload_trigger", data=0),
            # ── Bottom bar: pagination + actions ──
            html.Div(
                style={"display": "flex", "justifyContent": "space-between", "marginTop": "12px"},
                children=[
                    html.Div(
                        style={"display": "flex", "gap": "8px"},
                        children=[
                            html.Button("First Page", id="browse_first_page", n_clicks=0, className="sn-btn-secondary", style={"fontSize": "85%", "padding": "6px 16px"}),
                            html.Button("Next Page", id="browse_next_page", n_clicks=0, className="sn-btn-secondary", style={"fontSize": "85%", "padding": "6px 16px"}),
                        ],
                    ),
                    html.Div(
                        style={"display": "flex", "gap": "8px"},
                        children=[
                            html.Button("Edit Selected", id="browse_edit_button", n_clicks=0, className="sn-btn", style={"fontSize": "85%", "padding": "6px 16px"}),
                            html.Button("Delete Selected", id="browse_delete_button", n_clicks=0, className="sn-btn-danger", style={"fontSize": "85%", "padding": "6px 16px"}),
                        ],
                    ),
                ],
            ),
            # ── Status ──
            html.Div(id="browse_status_message", className="sn-results-area"),
            # ── Edit modal (overlay) ──
            html.Div(
                id="edit_modal_container",
                className="sn-modal-overlay",
                style={"display": "none"},
                children=[
                    html.Div(
                        id="edit_modal",
                        className="sn-modal-content",
                        style={"width": "55%", "maxWidth": "700px", "border": "2px solid #458e9f"},
                        children=[
                            html.Div(
                                style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "15px"},
                                children=[
                                    html.Span("Edit Data Point", style={"fontSize": "120%", "color": "white"}),
                                    html.Button("X", id="edit_cancel_button", n_clicks=0, style={
                                        "background": "transparent", "border": "none",
                                        "color": "gray", "fontSize": "120%", "cursor": "pointer",
                                    }),
                                ],
                            ),
                            dcc.Store(id="edit_point_id_store", data=""),
                            html.Div(
                                "Edit the JSON fields below. Only fields relevant to this collection type will be applied.",
                                className="sn-card-sub",
                            ),
                            dcc.Textarea(
                                id="edit_json_input",
                                className="sn-textarea",
                                style={"height": "220px"},
                            ),
                            html.Div(
                                html.Button("Save Changes", id="edit_save_button", n_clicks=0, className="sn-btn"),
                                style={"marginTop": "12px"},
                            ),
                            html.Div(id="edit_status_message", className="sn-results-area"),
                        ],
                    ),
                ],
            ),
            # ── Confirm dialogs ──
            dcc.ConfirmDialog(id="confirm_delete_single", message="Are you sure you want to delete this data point?"),
            dcc.ConfirmDialog(id="confirm_bulk_delete", message=""),
        ],
    )


# ── Main render ────────────────────────────────────────────────────────────


def render_ingestion_tab() -> list:
    """Build the full ingestion tab with three card sections."""
    return [
        html.Div(
            className="sn-tab-page",
            children=[
                html.Div("Ingestion Management", className="sn-tab-title"),
                _bulk_ingest_section(),
                _selective_upload_section(),
                _browse_manage_section(),
            ],
        ),
    ]

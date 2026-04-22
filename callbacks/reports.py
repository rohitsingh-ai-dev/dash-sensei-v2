"""Reports tab callbacks — KPI summary, report grid, charts, export, auto-refresh."""

from __future__ import annotations

import json
import logging

import pandas as pd
from dash import ALL, MATCH, Input, Output, State, ctx, dcc, html, no_update

from serving import app
from services import report_service
from utils.helpers import (
    CHART_TYPE_OPTIONS,
    GRAPH_CONFIG,
    auto_detect_chart_type,
    build_chart,
    build_data_table,
    detect_kpi_indicator,
)

logger = logging.getLogger(__name__)

# Aliases for backward compatibility within this module
_build_chart = build_chart
_GRAPH_CONFIG = GRAPH_CONFIG
_CHART_TYPE_OPTIONS = CHART_TYPE_OPTIONS


# ======================================================================
# KPI card builder (for summary row)
# ======================================================================


def _build_kpi_card(report: dict, kpi: dict) -> html.Div:
    """Build a single KPI summary card."""
    domain = report.get("domain", "")
    title = report.get("title", kpi["label"])

    return html.Div(
        className="rpt-kpi-card",
        children=[
            html.Div(kpi["formatted_value"], className="rpt-kpi-value"),
            html.Div(title, className="rpt-kpi-label", title=title),
            html.Div(f"[{domain}]", className="rpt-kpi-domain"),
        ],
    )


# ======================================================================
# Viz controls (expanded chart types, pre-populated defaults)
# ======================================================================


def _build_viz_controls(
    report_id: str,
    columns: list[str],
    auto_config: dict | None = None,
) -> html.Div:
    """Build inline chart controls with expanded chart types and defaults."""
    col_options = [{"label": c, "value": c} for c in columns]
    dd_style = {"width": "160px", "backgroundColor": "#1a212a", "fontSize": "85%"}

    default_chart = auto_config.get("chart_type") if auto_config else None
    default_x = auto_config.get("x_col") if auto_config else None
    default_y = auto_config.get("y_col") if auto_config else None

    return html.Details(
        [
            html.Summary("Chart Controls"),
            html.Div(
                className="rpt-viz-controls",
                children=[
                    html.Div([
                        html.Label("Chart Type"),
                        dcc.Dropdown(
                            id={"type": "viz_chart_type", "index": report_id},
                            options=_CHART_TYPE_OPTIONS,
                            value=default_chart,
                            placeholder="Select...",
                            style=dd_style,
                        ),
                    ]),
                    html.Div([
                        html.Label("X-axis"),
                        dcc.Dropdown(
                            id={"type": "viz_x_col", "index": report_id},
                            options=col_options,
                            value=default_x,
                            placeholder="Column...",
                            style=dd_style,
                        ),
                    ]),
                    html.Div([
                        html.Label("Y-axis"),
                        dcc.Dropdown(
                            id={"type": "viz_y_col", "index": report_id},
                            options=col_options,
                            value=default_y,
                            placeholder="Column...",
                            style=dd_style,
                        ),
                    ]),
                    html.Div([
                        html.Button(
                            "Update Chart",
                            id={"type": "viz_generate_btn", "index": report_id},
                            n_clicks=0,
                            style={"backgroundColor": "#458e9f", "border": "1px solid gray", "fontSize": "85%", "color": "white", "borderRadius": "6px", "padding": "6px 12px", "marginTop": "18px"},
                        ),
                    ]),
                    html.Div([
                        html.Button(
                            "Save Config",
                            id={"type": "viz_save_config_btn", "index": report_id},
                            n_clicks=0,
                            style={"backgroundColor": "#2a3340", "border": "1px solid #555", "fontSize": "85%", "color": "#c9d1d9", "borderRadius": "6px", "padding": "6px 12px", "marginTop": "18px"},
                        ),
                    ]),
                    html.Div(id={"type": "viz_save_msg", "index": report_id}, style={"fontSize": "85%", "color": "#388A98", "marginTop": "20px"}),
                ],
            ),
            html.Div(
                id={"type": "viz_chart_output", "index": report_id},
                style={"marginTop": "10px"},
            ),
        ],
    )


# ======================================================================
# Render report content (auto-detect chart + table + controls)
# ======================================================================


def _render_report_content(report: dict) -> html.Div:
    """Render the content area: auto-detected chart + table + viz controls."""
    results = report.get("results") or []
    report_id = report.get("report_id", "")

    if not results:
        return html.Div("Click Refresh to load data.", style={"color": "gray", "fontStyle": "italic"})

    df = pd.DataFrame(results)
    parts = []

    # Determine chart config: saved > auto-detected
    chart_type = report.get("chart_type")
    x_col = report.get("category_column")
    y_col = report.get("value_column")
    chart_title = report.get("chart_title")
    max_rows = report.get("max_rows")
    auto_config = None

    if not chart_type:
        auto_config = auto_detect_chart_type(df)
        if auto_config:
            chart_type = auto_config["chart_type"]
            x_col = auto_config["x_col"]
            y_col = auto_config["y_col"]

    # Render chart
    chart_result = _build_chart(results, chart_type, x_col, y_col, chart_title, max_rows, report_id)
    has_chart = isinstance(chart_result, dcc.Graph)
    if has_chart:
        parts.append(chart_result)
    elif isinstance(chart_result, str):
        logger.warning("Auto-chart failed for report %s: %s", report_id, chart_result)

    # Data table (collapsed if chart exists, open otherwise)
    table = build_data_table(results, table_id=f"report_table_{report_id}", page_size=5)
    if has_chart:
        parts.append(html.Details([
            html.Summary(f"Data Table ({len(results)} rows)"),
            table,
        ], style={"marginTop": "8px"}))
    else:
        parts.append(table)

    # Viz controls (collapsed, pre-populated with auto-detected or saved values)
    columns = list(df.columns)
    effective_config = auto_config or ({"chart_type": chart_type, "x_col": x_col, "y_col": y_col} if chart_type else None)
    parts.append(_build_viz_controls(report_id, columns, effective_config))

    # Data store for inline chart generation + CSV export
    parts.append(dcc.Store(id={"type": "viz_data_store", "index": report_id}, data=results))
    parts.append(dcc.Download(id={"type": "report_download", "index": report_id}))

    return html.Div(parts)


# ======================================================================
# Build report card (redesigned with header/body/footer)
# ======================================================================


def _build_report_card(report: dict) -> html.Div:
    """Render a single report card with header, body, footer."""
    report_id = report.get("report_id", "")
    title = report.get("title", "Untitled")
    domain = report.get("domain", "")
    sql = report.get("sql", "")
    updated_at = report.get("updated_at", "")

    # Format timestamp
    ts_display = ""
    if updated_at:
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
            ts_display = dt.strftime("%b %d, %I:%M %p")
        except Exception:
            ts_display = updated_at[:16]

    content = _render_report_content(report)

    return html.Div(
        className="rpt-card",
        id={"type": "report_card", "index": report_id},
        children=[
            # Header
            html.Div(
                className="rpt-card-header",
                children=[
                    html.Div([
                        html.Span(title, className="rpt-card-title"),
                        html.Span(f"[{domain}]", className="rpt-card-domain"),
                    ]),
                    html.Div(
                        className="rpt-card-actions",
                        children=[
                            html.Span(ts_display, className="rpt-card-timestamp"),
                            html.Button("Refresh", id={"type": "report_refresh_btn", "index": report_id}, n_clicks=0, className="rpt-btn-refresh"),
                            html.Button("Delete", id={"type": "report_delete_btn", "index": report_id}, n_clicks=0, className="rpt-btn-delete"),
                        ],
                    ),
                ],
            ),
            # Body
            html.Div(
                content,
                className="rpt-card-body",
                id={"type": "report_content_area", "index": report_id},
            ),
            # Footer
            html.Div(
                className="rpt-card-footer",
                children=[
                    html.Button("Export CSV", id={"type": "report_csv_btn", "index": report_id}, n_clicks=0),
                    html.Details([
                        html.Summary("SQL"),
                        html.Pre(sql, className="rpt-sql-block"),
                    ]),
                ],
            ),
        ],
    )


# ======================================================================
# Helpers for list rendering
# ======================================================================


def _fetch_and_render(domain: str | None = None) -> tuple[list, list]:
    """Fetch reports, return (kpi_cards, report_cards)."""
    try:
        data = report_service.list(domain=domain)
        reports = data.get("reports", [])
    except Exception as exc:
        logger.exception("Failed to list reports")
        err = [html.Div(f"Failed to load: {exc}", style={"color": "lightcoral"})]
        return [], err

    if not reports:
        return [], [html.Div("No saved reports yet.", className="rpt-empty")]

    kpi_cards = []
    report_cards = []
    for r in reports:
        results = r.get("results") or []
        kpi = detect_kpi_indicator(results)
        if kpi:
            kpi_cards.append(_build_kpi_card(r, kpi))
        report_cards.append(_build_report_card(r))

    return kpi_cards, report_cards


# ======================================================================
# Callback: Create report
# ======================================================================


@app.callback(
    Output("report_create_result", "children"),
    Output("loading-output-report-create", "children"),
    Output("report_title_input", "value"),
    Output("report_sql_input", "value"),
    Output("report_list_container", "children", allow_duplicate=True),
    Output("reports_kpi_cards_container", "children", allow_duplicate=True),
    Input("report_save_button", "n_clicks"),
    State("report_title_input", "value"),
    State("report_domain_selector", "value"),
    State("report_sql_input", "value"),
    State("report_chart_type", "value"),
    State("report_category_col", "value"),
    State("report_value_col", "value"),
    State("report_chart_title", "value"),
    prevent_initial_call=True,
)
def create_report(n_clicks, title, domain, sql, chart_type, cat_col, val_col, chart_title):
    """Save a new report via POST /reports, then refresh the list."""
    if not n_clicks:
        return no_update, "", no_update, no_update, no_update, no_update

    if not title or len(title.strip()) < 3:
        return "Title must be at least 3 characters.", "", no_update, no_update, no_update, no_update

    if not domain:
        return "Please select a domain.", "", no_update, no_update, no_update, no_update

    if not sql or not sql.strip():
        return "SQL query is required.", "", no_update, no_update, no_update, no_update

    try:
        result = report_service.create(
            title=title.strip(), domain=domain.upper(), sql=sql.strip(),
            chart_type=chart_type or None, category_column=cat_col or None,
            value_column=val_col or None, chart_title=chart_title or None,
        )
    except Exception as exc:
        logger.exception("Failed to create report")
        return f"Error: {exc}", "", no_update, no_update, no_update, no_update

    error = result.get("error")
    if error:
        return f"Backend error: {error}", "", no_update, no_update, no_update, no_update

    kpi_cards, report_cards = _fetch_and_render()
    return f"Report '{title}' saved!", "", "", "", report_cards, kpi_cards or no_update


# ======================================================================
# Callback: List / refresh reports (manual + domain filter)
# ======================================================================


@app.callback(
    Output("report_list_container", "children"),
    Output("reports_kpi_cards_container", "children"),
    Input("report_list_refresh_button", "n_clicks"),
    Input("report_list_domain_filter", "value"),
    prevent_initial_call=True,
)
def list_reports(n_clicks, domain_filter):
    """Fetch and render the reports list + KPI summary."""
    domain = domain_filter if domain_filter else None
    kpi_cards, report_cards = _fetch_and_render(domain)
    return report_cards, kpi_cards or [html.Div("No single-value reports.", className="rpt-subheading")]


# ======================================================================
# Callback: Auto-refresh toggle
# ======================================================================


@app.callback(
    Output("reports_auto_refresh_interval", "interval"),
    Output("reports_auto_refresh_interval", "disabled"),
    Input("reports_auto_refresh_toggle", "value"),
    prevent_initial_call=True,
)
def toggle_auto_refresh(interval_ms):
    """Enable/disable the auto-refresh interval."""
    if not interval_ms:
        return 300000, True
    return interval_ms, False


@app.callback(
    Output("report_list_container", "children", allow_duplicate=True),
    Output("reports_kpi_cards_container", "children", allow_duplicate=True),
    Input("reports_auto_refresh_interval", "n_intervals"),
    State("report_list_domain_filter", "value"),
    prevent_initial_call=True,
)
def auto_refresh_reports(n_intervals, domain_filter):
    """Periodically refresh all reports."""
    domain = domain_filter if domain_filter else None
    kpi_cards, report_cards = _fetch_and_render(domain)
    return report_cards, kpi_cards or [html.Div("No single-value reports.", className="rpt-subheading")]


# ======================================================================
# Callback: Refresh individual report
# ======================================================================


@app.callback(
    Output({"type": "report_content_area", "index": MATCH}, "children"),
    Input({"type": "report_refresh_btn", "index": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def refresh_single_report(n_clicks):
    """Re-execute the stored SQL and update the card content."""
    if not n_clicks:
        return no_update

    triggered = ctx.triggered_id
    report_id = triggered.get("index", "") if isinstance(triggered, dict) else ""
    if not report_id:
        return no_update

    try:
        result = report_service.refresh(report_id)
    except Exception as exc:
        logger.exception("Failed to refresh report %s", report_id)
        return html.Div(f"Refresh failed: {exc}", style={"color": "lightcoral"})

    if result.get("error"):
        return html.Div(f"Error: {result['error']}", style={"color": "lightcoral"})

    return _render_report_content(result)


# ======================================================================
# Callback: Generate inline chart
# ======================================================================


@app.callback(
    Output({"type": "viz_chart_output", "index": MATCH}, "children"),
    Input({"type": "viz_generate_btn", "index": MATCH}, "n_clicks"),
    State({"type": "viz_chart_type", "index": MATCH}, "value"),
    State({"type": "viz_x_col", "index": MATCH}, "value"),
    State({"type": "viz_y_col", "index": MATCH}, "value"),
    State({"type": "viz_data_store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def generate_inline_chart(n_clicks, chart_type, x_col, y_col, store_data):
    """Render a chart from user-selected columns."""
    if not n_clicks:
        return no_update

    logger.info(
        "generate_inline_chart: chart_type=%s x_col=%s y_col=%s store_data_type=%s store_data_len=%s",
        chart_type, x_col, y_col, type(store_data).__name__,
        len(store_data) if isinstance(store_data, (list, str)) else "N/A",
    )

    if not chart_type:
        return html.Div("Select a chart type.", style={"color": "lightcoral", "fontSize": "85%"})
    if not x_col:
        return html.Div("Select an X-axis column.", style={"color": "lightcoral", "fontSize": "85%"})
    if not y_col:
        return html.Div("Select a Y-axis column.", style={"color": "lightcoral", "fontSize": "85%"})
    if not store_data:
        return html.Div("No data available. Click Refresh first.", style={"color": "lightcoral", "fontSize": "85%"})

    data = store_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return html.Div("Failed to parse data.", style={"color": "lightcoral", "fontSize": "85%"})

    triggered = ctx.triggered_id
    report_id = triggered.get("index", "") if isinstance(triggered, dict) else ""

    logger.info(
        "generate_inline_chart: building chart for report_id=%s rows=%d cols=%s",
        report_id, len(data), list(data[0].keys()) if data else "empty",
    )

    result = _build_chart(data, chart_type, x_col, y_col, report_id=report_id)
    if isinstance(result, str):
        logger.warning("generate_inline_chart error: %s", result)
        return html.Div(result, style={"color": "lightcoral", "fontSize": "85%"})
    if result is not None:
        return result
    return html.Div("Could not generate chart.", style={"color": "lightcoral", "fontSize": "85%"})


# ======================================================================
# Callback: CSV export
# ======================================================================


@app.callback(
    Output({"type": "report_download", "index": MATCH}, "data"),
    Input({"type": "report_csv_btn", "index": MATCH}, "n_clicks"),
    State({"type": "viz_data_store", "index": MATCH}, "data"),
    prevent_initial_call=True,
)
def export_csv(n_clicks, store_data):
    """Export report data as CSV download."""
    if not n_clicks or not store_data:
        return no_update

    data = store_data
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return no_update

    df = pd.DataFrame(data)
    return dcc.send_data_frame(df.to_csv, "report_export.csv", index=False)


# ======================================================================
# Callback: Save chart config (PATCH)
# ======================================================================


@app.callback(
    Output({"type": "viz_save_msg", "index": MATCH}, "children"),
    Input({"type": "viz_save_config_btn", "index": MATCH}, "n_clicks"),
    State({"type": "viz_chart_type", "index": MATCH}, "value"),
    State({"type": "viz_x_col", "index": MATCH}, "value"),
    State({"type": "viz_y_col", "index": MATCH}, "value"),
    prevent_initial_call=True,
)
def save_chart_config(n_clicks, chart_type, x_col, y_col):
    """Save the chart configuration to the report via PATCH."""
    if not n_clicks:
        return no_update

    triggered = ctx.triggered_id
    report_id = triggered.get("index", "") if isinstance(triggered, dict) else ""
    if not report_id:
        return no_update

    try:
        report_service.update(
            report_id,
            chart_type=chart_type,
            category_column=x_col,
            value_column=y_col,
        )
        return "Config saved!"
    except Exception as exc:
        logger.exception("Failed to save chart config for %s", report_id)
        return f"Save failed: {exc}"


# ======================================================================
# Callback: Delete individual report
# ======================================================================


@app.callback(
    Output({"type": "report_card", "index": MATCH}, "style"),
    Input({"type": "report_delete_btn", "index": MATCH}, "n_clicks"),
    prevent_initial_call=True,
)
def delete_single_report(n_clicks):
    """Delete a report and hide its card."""
    if not n_clicks:
        return no_update

    triggered = ctx.triggered_id
    report_id = triggered.get("index", "") if isinstance(triggered, dict) else ""
    if not report_id:
        return no_update

    try:
        report_service.delete(report_id)
    except Exception as exc:
        logger.exception("Failed to delete report %s", report_id)
        return no_update

    return {"display": "none"}

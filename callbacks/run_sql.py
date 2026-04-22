"""Run SQL tab callback — execute raw SQL and display results."""

from __future__ import annotations

import logging

from dash import Input, Output, State, html, no_update

from serving import app
from services import query_service
from utils.helpers import build_data_table

logger = logging.getLogger(__name__)


@app.callback(
    Output("runsql_output_container", "children"),
    Output("loading-output-runsql", "children"),
    Input("runsql_submit_button", "n_clicks"),
    State("runsql_input", "value"),
    State("runsql_domain_selector", "value"),
    prevent_initial_call=True,
)
def execute_sql(n_clicks, sql, domain):
    """Execute raw SQL via POST /execute and render results."""
    if not n_clicks:
        return no_update, ""

    if not sql or not sql.strip():
        return (
            html.Div("Please enter a SQL query.", style={"color": "lightcoral"}),
            "",
        )

    logger.info("Executing raw SQL: %s...", sql[:100])

    try:
        result = query_service.execute_sql(sql.strip(), domain=domain)
    except Exception as exc:
        logger.exception("SQL execution failed")
        return (
            html.Div(f"Execution failed: {exc}", style={"color": "lightcoral"}),
            "",
        )

    error = result.get("error")
    if error:
        return (
            html.Div(f"Error: {error}", style={"color": "lightcoral"}),
            "",
        )

    results_data = result.get("results", [])
    row_count = result.get("row_count", 0)

    if results_data:
        table = build_data_table(results_data, table_id="runsql_data_table", page_size=10)
        output = html.Div(
            [
                html.Div(
                    f"Returned {row_count} row(s).",
                    style={"color": "#458e9f", "marginBottom": "10px"},
                ),
                table,
            ]
        )
    else:
        output = html.Div("Query returned no results.", style={"color": "gray"})

    return output, ""

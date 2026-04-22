"""Ingestion tab callbacks — bulk ingest, selective upload, browse & manage."""

from __future__ import annotations

import json
import logging

from dash import Input, Output, State, ctx, html, no_update
from dash.exceptions import PreventUpdate

from serving import app
from services import ingest_service

logger = logging.getLogger(__name__)

# Full style dicts for the edit modal overlay — must include all positioning
# properties because Dash replaces the entire style dict on each update.
_MODAL_VISIBLE = {
    "display": "block",
    "position": "fixed",
    "top": "0",
    "left": "0",
    "width": "100vw",
    "height": "100vh",
    "backgroundColor": "rgba(0,0,0,0.6)",
    "zIndex": "9999",
}

_MODAL_HIDDEN = {
    "display": "none",
    "position": "fixed",
    "top": "0",
    "left": "0",
    "width": "100vw",
    "height": "100vh",
    "backgroundColor": "rgba(0,0,0,0.6)",
    "zIndex": "9999",
}


# ======================================================================
# Helper: build table row data from a datapoint item
# ======================================================================


def _datapoint_to_row(item: dict) -> dict:
    """Convert a DatapointResponse dict to a flat table row showing ALL fields."""
    payload = item.get("payload", {})
    collection = item.get("collection", "")

    if collection == "schema":
        return {
            "point_id": item.get("point_id", ""),
            "domain": item.get("domain", ""),
            "table": payload.get("table_name", ""),
            "column": payload.get("column_name", ""),
            "type": payload.get("data_type", ""),
            "description": payload.get("description", ""),
            "usage": payload.get("usage", ""),
        }
    elif collection == "kpi":
        return {
            "point_id": item.get("point_id", ""),
            "domain": item.get("domain", ""),
            "kpi_name": payload.get("kpi_name", ""),
            "table": payload.get("table", ""),
            "sql_formula": payload.get("sql_formula", ""),
            "description": payload.get("description", ""),
        }
    elif collection == "glossary":
        return {
            "point_id": item.get("point_id", ""),
            "domain": item.get("domain", ""),
            "term": payload.get("term", ""),
            "definition": payload.get("definition", ""),
        }
    else:
        # Generic fallback — show all payload keys
        row = {
            "point_id": item.get("point_id", ""),
            "domain": item.get("domain", ""),
        }
        for k, v in payload.items():
            if k != "content_hash":
                row[k] = str(v)[:200] if isinstance(v, (str, list, dict)) else v
        return row


# ======================================================================
# 1. Bulk re-ingest
# ======================================================================


@app.callback(
    Output("ingest_output_container", "children"),
    Output("loading-output-ingest", "children"),
    Input("ingest_submit_button", "n_clicks"),
    prevent_initial_call=True,
)
def trigger_ingestion(n_clicks):
    """Trigger domain config ingestion via POST /ingest."""
    if not n_clicks:
        return no_update, ""

    logger.info("Triggering domain config ingestion...")

    try:
        result = ingest_service.trigger()
    except Exception as exc:
        logger.exception("Ingestion failed")
        return (
            html.Div(f"Ingestion failed: {exc}", style={"color": "lightcoral"}),
            "",
        )

    domains = result.get("domains_processed", [])
    schema_count = result.get("schema_count", {})
    kpi_count = result.get("kpi_count", {})
    glossary_count = result.get("glossary_count", {})
    duration = result.get("duration_seconds", 0)
    verified = result.get("verification_passed", False)

    rows = []
    for d in domains:
        rows.append(
            html.Tr(
                [
                    html.Td(d, style={"padding": "5px 15px"}),
                    html.Td(str(schema_count.get(d, 0)), style={"padding": "5px 15px"}),
                    html.Td(str(kpi_count.get(d, 0)), style={"padding": "5px 15px"}),
                    html.Td(str(glossary_count.get(d, 0)), style={"padding": "5px 15px"}),
                ]
            )
        )

    badge_color = "#4CAF50" if verified else "#f44336"
    badge_text = "PASSED" if verified else "FAILED"

    output = html.Div(
        [
            html.Div(
                f"Ingestion completed in {duration:.1f} seconds.",
                style={"color": "#458e9f", "marginBottom": "10px", "fontSize": "110%"},
            ),
            html.Table(
                [
                    html.Thead(
                        html.Tr(
                            [
                                html.Th("Domain", style={"padding": "5px 15px"}),
                                html.Th("Schema", style={"padding": "5px 15px"}),
                                html.Th("KPIs", style={"padding": "5px 15px"}),
                                html.Th("Glossary", style={"padding": "5px 15px"}),
                            ]
                        )
                    ),
                    html.Tbody(rows),
                ],
                style={
                    "color": "white",
                    "border": "1px solid gray",
                    "borderCollapse": "collapse",
                    "marginBottom": "15px",
                },
            ),
            html.Div(
                [
                    html.Span("Verification: ", style={"color": "white"}),
                    html.Span(
                        badge_text,
                        style={
                            "color": "white",
                            "backgroundColor": badge_color,
                            "padding": "3px 10px",
                            "borderRadius": "10px",
                            "fontSize": "90%",
                        },
                    ),
                ]
            ),
        ]
    )

    return output, ""


# ======================================================================
# 2. Selective upload
# ======================================================================


@app.callback(
    Output("upload_output_container", "children"),
    Output("loading-output-upload", "children"),
    Input("upload_submit_button", "n_clicks"),
    State("upload_domain", "value"),
    State("upload_type", "value"),
    State("upload_json_input", "value"),
    prevent_initial_call=True,
)
def selective_upload(n_clicks, domain, collection_type, json_text):
    """Parse JSON input and call the appropriate selective ingest endpoint."""
    if not n_clicks:
        return no_update, ""

    if not json_text or not json_text.strip():
        return html.Div("Please paste a JSON array.", style={"color": "lightcoral"}), ""

    try:
        items = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return html.Div(f"Invalid JSON: {exc}", style={"color": "lightcoral"}), ""

    if not isinstance(items, list) or not items:
        return html.Div("Input must be a non-empty JSON array.", style={"color": "lightcoral"}), ""

    try:
        if collection_type == "schema":
            result = ingest_service.ingest_schema(domain, items)
        elif collection_type == "kpi":
            result = ingest_service.ingest_kpis(domain, items)
        elif collection_type == "glossary":
            result = ingest_service.ingest_glossary(domain, items)
        else:
            return html.Div(f"Unknown type: {collection_type}", style={"color": "lightcoral"}), ""
    except Exception as exc:
        logger.exception("Selective upload failed")
        return html.Div(f"Upload failed: {exc}", style={"color": "lightcoral"}), ""

    count = result.get("ingested_count", 0)
    point_ids = result.get("point_ids", [])
    ids_preview = ", ".join(point_ids[:5])
    if len(point_ids) > 5:
        ids_preview += f" ... (+{len(point_ids) - 5} more)"

    return (
        html.Div(
            [
                html.Div(
                    f"Successfully ingested {count} {collection_type} item(s) for {domain}.",
                    style={"color": "#4CAF50", "marginBottom": "5px"},
                ),
                html.Div(
                    f"Point IDs: {ids_preview}",
                    style={"color": "#aaa", "fontSize": "85%"},
                ),
            ]
        ),
        "",
    )


# ======================================================================
# 3. Browse & load data points
#
# Uses a hidden trigger div instead of bumping n_clicks on the Load
# button.  Load / First Page / Next Page all fire this callback.
# Other callbacks write to "browse_reload_trigger" to request a refresh.
# ======================================================================


@app.callback(
    Output("browse_table", "data"),
    Output("browse_table", "columns"),
    Output("browse_data_store", "data"),
    Output("browse_cursor_store", "data"),
    Output("browse_total_count", "children"),
    Output("browse_status_message", "children", allow_duplicate=True),
    Input("browse_load_button", "n_clicks"),
    Input("browse_first_page", "n_clicks"),
    Input("browse_next_page", "n_clicks"),
    Input("browse_reload_trigger", "data"),
    State("browse_collection", "value"),
    State("browse_domain", "value"),
    State("browse_cursor_store", "data"),
    prevent_initial_call=True,
)
def browse_datapoints(
    load_clicks, first_clicks, next_clicks, reload_trigger,
    collection, domain, current_cursor,
):
    """Load data points from the browse endpoint with cursor pagination."""
    triggered_id = ctx.triggered_id

    if triggered_id in ("browse_load_button", "browse_first_page", "browse_reload_trigger"):
        cursor = None  # first page
    elif triggered_id == "browse_next_page":
        cursor = current_cursor
        if cursor is None:
            raise PreventUpdate
    else:
        raise PreventUpdate

    domain_filter = domain if domain else None

    try:
        # Fewshots are stored in domain config, not a separate Qdrant collection
        if collection == "fewshots":
            if not domain_filter:
                return [], no_update, [], None, "Select a domain to view few-shot examples", ""
            result = ingest_service.list_fewshots(domain_filter)
            fewshots = result.get("fewshots", [])
            table_data = [
                {"index": i + 1, "domain": domain_filter, "question": fs.get("question", ""), "sql": fs.get("sql", "")}
                for i, fs in enumerate(fewshots)
            ]
            columns = [
                {"name": "#", "id": "index"},
                {"name": "Domain", "id": "domain"},
                {"name": "Question", "id": "question"},
                {"name": "SQL", "id": "sql"},
            ]
            count_text = f"Total: {len(fewshots)} few-shot examples"
            return table_data, columns, [], None, count_text, ""

        result = ingest_service.list_datapoints(
            collection=collection,
            domain=domain_filter,
            cursor=cursor,
            limit=50,
        )
    except Exception as exc:
        logger.exception("Browse datapoints failed")
        return [], no_update, [], None, "", html.Div(f"Load failed: {exc}", style={"color": "lightcoral"})

    items = result.get("items", [])
    total = result.get("total", 0)
    next_cursor = result.get("next_cursor")

    table_data = [_datapoint_to_row(item) for item in items]

    # Build dynamic columns from the first row's keys
    if table_data:
        columns = [{"name": k.replace("_", " ").title(), "id": k} for k in table_data[0].keys()]
    else:
        columns = [{"name": "Point ID", "id": "point_id"}, {"name": "Domain", "id": "domain"}]

    count_text = f"Total: {total} data points"
    if next_cursor:
        count_text += "  |  More pages available"
    else:
        count_text += "  |  Last page"

    return table_data, columns, items, next_cursor, count_text, ""


# ======================================================================
# 4. Edit modal — open / close
# ======================================================================


@app.callback(
    Output("edit_modal_container", "style"),
    Output("edit_json_input", "value"),
    Output("edit_point_id_store", "data"),
    Output("edit_status_message", "children", allow_duplicate=True),
    Input("browse_edit_button", "n_clicks"),
    Input("edit_cancel_button", "n_clicks"),
    State("browse_table", "selected_rows"),
    State("browse_data_store", "data"),
    State("browse_collection", "value"),
    prevent_initial_call=True,
)
def toggle_edit_modal(edit_clicks, cancel_clicks, selected_rows, data_store, collection):
    """Open or close the edit modal."""
    triggered_id = ctx.triggered_id

    if triggered_id == "edit_cancel_button":
        return _MODAL_HIDDEN, "", "", ""

    if triggered_id == "browse_edit_button":
        if not selected_rows or not data_store:
            return no_update, no_update, no_update, html.Div(
                "Select a row first, then click Edit.", style={"color": "#aaa"}
            )

        idx = selected_rows[0]
        if idx >= len(data_store):
            return no_update, no_update, no_update, no_update

        item = data_store[idx]
        point_id = item.get("point_id", "")
        payload = item.get("payload", {})

        if collection == "schema":
            editable = {
                "table_name": payload.get("table_name", ""),
                "column_name": payload.get("column_name", ""),
                "data_type": payload.get("data_type", ""),
                "description": payload.get("description", ""),
                "usage": payload.get("usage", ""),
            }
            if payload.get("examples"):
                editable["examples"] = payload["examples"]
            if payload.get("role"):
                editable["role"] = payload["role"]
        elif collection == "kpi":
            editable = {
                "kpi_name": payload.get("kpi_name", ""),
                "description": payload.get("description", ""),
                "sql_formula": payload.get("sql_formula", ""),
                "table": payload.get("table", ""),
            }
            if payload.get("related_columns"):
                editable["related_columns"] = payload["related_columns"]
        else:
            editable = {
                "term": payload.get("term", ""),
                "definition": payload.get("definition", ""),
            }

        json_text = json.dumps(editable, indent=2)
        return _MODAL_VISIBLE, json_text, point_id, ""

    raise PreventUpdate


# ======================================================================
# 5. Edit modal — save
# ======================================================================


@app.callback(
    Output("edit_modal_container", "style", allow_duplicate=True),
    Output("edit_status_message", "children"),
    Output("browse_reload_trigger", "data", allow_duplicate=True),
    Input("edit_save_button", "n_clicks"),
    State("edit_point_id_store", "data"),
    State("edit_json_input", "value"),
    State("browse_collection", "value"),
    State("browse_reload_trigger", "data"),
    prevent_initial_call=True,
)
def save_edit(n_clicks, point_id, json_text, collection, current_trigger):
    """Save edits — calls PUT endpoint, then triggers a browse reload."""
    if not n_clicks or not point_id:
        raise PreventUpdate

    try:
        update_data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return no_update, html.Div(f"Invalid JSON: {exc}", style={"color": "lightcoral"}), no_update

    update_data["collection"] = collection

    try:
        result = ingest_service.update_datapoint(point_id, collection, update_data)
    except Exception as exc:
        logger.exception("Update datapoint failed")
        return no_update, html.Div(f"Update failed: {exc}", style={"color": "lightcoral"}), no_update

    new_id = result.get("point_id", "")
    logger.info("Updated datapoint %s -> %s", point_id, new_id)

    return _MODAL_HIDDEN, "", (current_trigger or 0) + 1


# ======================================================================
# 6. Single delete — confirm + execute
# ======================================================================


@app.callback(
    Output("confirm_delete_single", "displayed"),
    Output("browse_status_message", "children", allow_duplicate=True),
    Input("browse_delete_button", "n_clicks"),
    State("browse_table", "selected_rows"),
    prevent_initial_call=True,
)
def ask_confirm_single_delete(n_clicks, selected_rows):
    """Show confirmation dialog when delete button is clicked."""
    if not n_clicks:
        return False, no_update
    if not selected_rows:
        return False, html.Div("Select a row first, then click Delete.", style={"color": "#aaa"})
    return True, no_update


@app.callback(
    Output("browse_status_message", "children", allow_duplicate=True),
    Output("browse_reload_trigger", "data", allow_duplicate=True),
    Input("confirm_delete_single", "submit_n_clicks"),
    State("browse_table", "selected_rows"),
    State("browse_data_store", "data"),
    State("browse_collection", "value"),
    State("browse_reload_trigger", "data"),
    prevent_initial_call=True,
)
def execute_single_delete(submit_clicks, selected_rows, data_store, collection, current_trigger):
    """Delete the selected data point after confirmation."""
    if not submit_clicks or not selected_rows or not data_store:
        raise PreventUpdate

    idx = selected_rows[0]
    if idx >= len(data_store):
        raise PreventUpdate

    point_id = data_store[idx].get("point_id", "")

    try:
        ingest_service.delete_datapoint(point_id, collection)
    except Exception as exc:
        logger.exception("Delete datapoint failed")
        return html.Div(f"Delete failed: {exc}", style={"color": "lightcoral"}), no_update

    return (
        html.Div(f"Deleted data point {point_id[:12]}...", style={"color": "#4CAF50"}),
        (current_trigger or 0) + 1,
    )


# ======================================================================
# 7. Bulk delete — confirm + execute
# ======================================================================


@app.callback(
    Output("confirm_bulk_delete", "displayed"),
    Output("confirm_bulk_delete", "message"),
    Input("browse_bulk_delete_button", "n_clicks"),
    State("browse_collection", "value"),
    State("browse_domain", "value"),
    prevent_initial_call=True,
)
def ask_confirm_bulk_delete(n_clicks, collection, domain):
    """Show confirmation dialog for bulk delete."""
    if not n_clicks:
        return False, ""
    if not domain:
        return False, ""

    msg = f"Delete ALL {collection} data points for domain '{domain}'? This cannot be undone."
    return True, msg


@app.callback(
    Output("browse_status_message", "children"),
    Output("browse_reload_trigger", "data"),
    Input("confirm_bulk_delete", "submit_n_clicks"),
    State("browse_collection", "value"),
    State("browse_domain", "value"),
    State("browse_reload_trigger", "data"),
    prevent_initial_call=True,
)
def execute_bulk_delete(submit_clicks, collection, domain, current_trigger):
    """Execute bulk delete after confirmation."""
    if not submit_clicks or not domain:
        raise PreventUpdate

    try:
        result = ingest_service.bulk_delete(collection, domain)
    except Exception as exc:
        logger.exception("Bulk delete failed")
        return html.Div(f"Bulk delete failed: {exc}", style={"color": "lightcoral"}), no_update

    count = result.get("deleted_count", 0)
    return (
        html.Div(
            f"Deleted {count} {collection} data points for {domain}.",
            style={"color": "#4CAF50"},
        ),
        (current_trigger or 0) + 1,
    )

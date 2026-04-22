"""KPI query callbacks — clean conversational flow.

Results render as cards with inline actions (View SQL, Save, Re-ask).
No sidebar, no fixed panels, no progress bar — typing indicator only.
"""

from __future__ import annotations

import logging
import threading
import uuid

import pandas as pd
from dash import (
    ALL,
    Input,
    Output,
    State,
    ctx,
    dcc,
    html,
    no_update,
)

from serving import app
from services import query_service, report_service
from services.query_stream_service import stream_query
from utils.cache import get_query_state, set_query_state
from utils.constants import QUESTIONS_BY_DOMAIN
from utils.helpers import auto_detect_chart_type, build_chart, build_data_table

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# Chat bubble helpers
# ═══════════════════════════════════════════════════════════════════════


def _sensei(text):
    """Assistant message row."""
    return html.Div(className="cx-row", children=[
        html.Div("S", className="cx-av cx-av-s"),
        html.Div(text, className="cx-bub cx-bub-s"),
    ])


def _user(text):
    """User message row."""
    return html.Div(className="cx-row cx-row-u", children=[
        html.Div("U", className="cx-av cx-av-u"),
        html.Div(text, className="cx-bub cx-bub-u"),
    ])


def _error(text):
    """Error message row."""
    return html.Div(className="cx-row", children=[
        html.Div("S", className="cx-av cx-av-s"),
        html.Div(text, className="cx-bub cx-bub-err"),
    ])


def _typing(status="Thinking"):
    """Typing indicator row."""
    return html.Div(className="cx-row", children=[
        html.Div("S", className="cx-av cx-av-s"),
        html.Div(status, className="cx-bub cx-bub-typing"),
    ])


def _result_card(results_data, sql, row_count, time_str):
    """Full result card: optional auto-chart + table + actions + SQL block + save."""
    table = build_data_table(results_data, table_id=f"tbl_{uuid.uuid4().hex[:8]}")

    # Attempt auto-chart
    chart_component = None
    try:
        df = pd.DataFrame(results_data)
        auto = auto_detect_chart_type(df)
        if auto:
            chart_result = build_chart(
                results_data, auto["chart_type"], auto["x_col"], auto["y_col"],
                report_id=f"chat_{uuid.uuid4().hex[:6]}",
            )
            if chart_result is not None and not isinstance(chart_result, str):
                chart_component = chart_result
    except Exception:
        pass  # silently fall back to table-only

    # Layout: chart (if any) + collapsed table, or just table
    if chart_component:
        content_parts = [
            chart_component,
            html.Details([
                html.Summary(f"Data Table ({row_count} rows)"),
                html.Div(table, className="cx-result-table"),
            ], style={"marginTop": "8px"}),
        ]
    else:
        content_parts = [html.Div(table, className="cx-result-table")]

    # Build the styled SQL block with toolbar
    sql_block = html.Div(
        id="inline_sql_block",
        className="cx-sql-wrap",
        style={"display": "none"},
        children=[
            html.Div(className="cx-sql-toolbar", children=[
                html.Span("SQL", className="cx-sql-lang"),
                html.Button("Copy", id="act_copy_sql", n_clicks=0, className="cx-sql-copy"),
            ]),
            html.Pre(sql, className="cx-sql-block"),
        ],
    )

    card_children = [
        *content_parts,
        html.Div(className="cx-actions", children=[
            html.Button("< > View SQL", id="act_view_sql", n_clicks=0),
            html.Button("Save to Reports", id="act_save", n_clicks=0),
        ]),
        sql_block,
        html.Div(
            id="inline_save_row",
            className="cx-save-inline",
            children=[
                dcc.Input(id="inline_save_title", type="text", placeholder="Title (min 3 chars)"),
                html.Button("Save", id="inline_save_btn", n_clicks=0),
            ],
            style={"display": "none"},
        ),
        html.Div(id="inline_save_msg", className="cx-save-ok"),
    ]

    return html.Div(className="cx-result-card", children=card_children)


# ═══════════════════════════════════════════════════════════════════════
# Background query runner
# ═══════════════════════════════════════════════════════════════════════


def _run_query_background(query_id, question, source, cust, whse, session_id):
    """Stream the query via SSE, writing per-step progress to cache."""
    stream_query(
        query_id=query_id,
        question=question,
        source=source,
        cust=cust or None,
        whse=whse or None,
        session_id=session_id,
    )


# ═══════════════════════════════════════════════════════════════════════
# Source change → load customers, reset chat
# ═══════════════════════════════════════════════════════════════════════


@app.callback(
    Output("welcome_message", "children"),
    Output("kpi_questions_parent", "children"),
    Output("kpi_questions_parent", "style"),
    Output("cust_input", "options"),
    Output("cust_input", "value"),
    Output("cust_input", "disabled"),
    Output("whse_input", "options"),
    Output("whse_input", "value"),
    Output("whse_input", "disabled"),
    Output("warehouse_id_map", "data"),
    Output("kpi_output_container", "children", allow_duplicate=True),
    Output("chat_history_list", "children", allow_duplicate=True),
    Input("source_selector", "value"),
    prevent_initial_call=True,
)
def on_source_change(source):
    spacer = html.Div(className="cx-spacer")
    empty_chat = [spacer, _sensei("Select a source above to get started.")]

    if source is None:
        return (
            "", [], {"display": "none"},
            [], None, True, [], None, True, {},
            empty_chat, [],
        )

    domain_key = source.upper()

    customers = []
    try:
        raw = query_service.get_customers(source)
        customers = [{"label": c["label"], "value": c["value"]} for c in raw if c.get("value")]
    except Exception:
        logger.warning("Failed to load customers for source=%s", source)

    greetings = {
        "LM": "You selected Labor Management. Pick a customer and warehouse, then ask me about KPIs, utilization, or hours.",
        "WMS": "You selected Warehouse Management. Pick a customer and warehouse, then ask about shipments, picks, or metrics.",
        "HR": "You selected Human Resources. Ask me about headcount, turnover, or any HR metric.",
    }
    chat = [html.Div(className="cx-spacer"), _sensei(greetings.get(domain_key, "Ready! Ask me a question."))]

    return (
        "", [], {"display": "none"},
        customers, None, False,
        [], None, True,
        {},
        chat, [],
    )


# ═══════════════════════════════════════════════════════════════════════
# Customer change → load warehouses
# ═══════════════════════════════════════════════════════════════════════


@app.callback(
    Output("whse_input", "options", allow_duplicate=True),
    Output("whse_input", "value", allow_duplicate=True),
    Output("whse_input", "disabled", allow_duplicate=True),
    Output("warehouse_id_map", "data", allow_duplicate=True),
    Input("cust_input", "value"),
    State("source_selector", "value"),
    prevent_initial_call=True,
)
def on_customer_change(cust, source):
    if not cust or not source:
        return [], None, True, {}
    try:
        wmap = query_service.get_warehouses(source, cust)
    except Exception:
        return [], None, True, {}

    opts = [{"label": n.title(), "value": n} for n in sorted(wmap.keys())]
    return opts, None, False, wmap


# ═══════════════════════════════════════════════════════════════════════
# Question autofill (kept for hidden compatibility)
# ═══════════════════════════════════════════════════════════════════════


@app.callback(
    Output("kpi_input", "value"),
    Input({"type": "kpi_questions", "index": ALL}, "n_clicks"),
    State("source_selector", "value"),
    prevent_initial_call=True,
)
def autofill(n_clicks, source):
    t = ctx.triggered_id
    if t is None or all(x is None for x in n_clicks):
        return no_update
    qs = QUESTIONS_BY_DOMAIN.get((source or "").upper(), [])
    idx = t.get("index", 0) if isinstance(t, dict) else 0
    return qs[idx] if 0 <= idx < len(qs) else no_update


# ═══════════════════════════════════════════════════════════════════════
# Submit question
# ═══════════════════════════════════════════════════════════════════════


@app.callback(
    Output("kpi_output_container", "children", allow_duplicate=True),
    Output("loading-output-kpi", "children", allow_duplicate=True),
    Output("source_selector", "style"),
    Output("kpi_input", "style"),
    Output("progress_bar", "value", allow_duplicate=True),
    Output("progress_bar", "animated", allow_duplicate=True),
    Output("progress_status", "children", allow_duplicate=True),
    Output("query_id", "data", allow_duplicate=True),
    Output("kpi_output_container_save", "style", allow_duplicate=True),
    Output("kpi_input", "value", allow_duplicate=True),
    Output("chat_history_list", "children", allow_duplicate=True),
    Input("submit_kpi_button", "n_clicks"),
    Input("kpi_input", "n_submit"),
    State("kpi_input", "value"),
    State("source_selector", "value"),
    State("cust_input", "value"),
    State("whse_input", "value"),
    State("session_id", "data"),
    State("warehouse_id_map", "data"),
    State("kpi_output_container", "children"),
    State("chat_history_list", "children"),
    prevent_initial_call=True,
)
def submit_question(
    n_clicks, n_submit, question, source, cust, whse, session_id,
    wmap, chat, history,
):
    hide = {"display": "none"}
    ns = {}

    if n_clicks == 0 and (n_submit == 0 or n_submit is None):
        return (no_update, "", ns, ns, 0, False, no_update, no_update, hide, no_update, no_update)

    if not source:
        c = list(chat or [])
        c.append(_error("Please select a Source first."))
        return (c, "", ns, ns, 0, False, no_update, no_update, hide, no_update, no_update)

    if not question:
        return (no_update, "", ns, ns, 0, False, no_update, no_update, hide, no_update, no_update)

    resolved_whse = whse
    if whse and wmap and isinstance(wmap, dict):
        resolved_whse = wmap.get(whse, whse)

    qid = str(uuid.uuid4())
    threading.Thread(
        target=_run_query_background,
        args=(qid, question, source, cust, resolved_whse, session_id),
        daemon=True,
    ).start()

    c = list(chat or [])
    c.append(_user(question))
    c.append(_typing("Searching knowledge base"))

    h = list(history or [])
    h.insert(0, html.Div(question[:60] + ("..." if len(question) > 60 else ""), className="chat-history-item"))

    return (c, "", ns, ns, 5, True, "Working...", qid, hide, "", h)


# ═══════════════════════════════════════════════════════════════════════
# Progress polling
# ═══════════════════════════════════════════════════════════════════════


@app.callback(
    Output("progress_bar", "value", allow_duplicate=True),
    Output("progress_bar", "animated", allow_duplicate=True),
    Output("progress_status", "children", allow_duplicate=True),
    Output("kpi_output_container", "children", allow_duplicate=True),
    Output("query_id", "data", allow_duplicate=True),
    Output("kpi_last_query_sql", "data"),
    Output("kpi_last_query_df", "data"),
    Output("kpi_output_container_save", "style", allow_duplicate=True),
    Output("chat_sql_store", "data"),
    Input("interval-component", "n_intervals"),
    State("query_id", "data"),
    State("kpi_output_container", "children"),
    prevent_initial_call=True,
)
def poll_progress(n, qid, chat):
    hide = {"display": "none"}
    noop = (no_update,) * 9

    if not qid:
        return noop

    state = get_query_state(qid)
    if state is None:
        return (5, True, "Working...", no_update, qid, no_update, no_update, hide, no_update)

    # Still running → update typing indicator
    if not state["completed"]:
        c = list(chat or [])
        if c:
            c[-1] = _typing(state["status"])
        return (state["progress"], True, state["status"], c, qid, no_update, no_update, hide, no_update)

    # ── Done ─────────────────────────────────────────────────────
    c = list(chat or [])
    if c:
        c.pop()  # remove typing

    if state.get("error"):
        c.append(_error(f"Something went wrong: {state['error']}"))
        return (100, False, "", c, None, no_update, no_update, hide, "")

    result = state.get("result", {})
    data = result.get("results") or []
    sql = result.get("sql", "")
    err = result.get("error")
    timing = result.get("timing") or {}
    total_ms = timing.get("total_ms", 0)
    ts = f" ({total_ms/1000:.1f}s)" if total_ms else ""

    if err:
        friendly = result.get("user_message") or err
        c.append(_error(friendly))
        return (100, False, "", c, None, no_update, no_update, hide, sql)

    if data:
        rc = result.get("row_count", len(data))
        c.append(_sensei(f"Found {rc} result(s){ts}:"))
        c.append(_result_card(data, sql, rc, ts))
        df_json = pd.DataFrame(data).to_json()
    else:
        c.append(_sensei(f"The query returned no results{ts}. Try rephrasing or adjusting filters."))
        df_json = None

    return (100, False, "", c, None, sql, df_json, hide, sql)


# ═══════════════════════════════════════════════════════════════════════
# Inline actions: View SQL toggle
# ═══════════════════════════════════════════════════════════════════════


@app.callback(
    Output("inline_sql_block", "style"),
    Input("act_view_sql", "n_clicks"),
    State("inline_sql_block", "style"),
    prevent_initial_call=True,
)
def toggle_sql(n, cur):
    if not n:
        return no_update
    cur = cur or {}
    if cur.get("display") == "none":
        return {"display": "block"}
    return {"display": "none"}


# Copy SQL to clipboard (client-side)
app.clientside_callback(
    """
    function(n) {
        if (!n) return window.dash_clientside.no_update;
        var el = document.querySelector('.cx-sql-block');
        if (el) {
            navigator.clipboard.writeText(el.textContent).then(function() {
                var btn = document.getElementById('act_copy_sql');
                if (btn) { btn.textContent = 'Copied!'; setTimeout(function(){ btn.textContent = 'Copy'; }, 1500); }
            });
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("act_copy_sql", "className"),
    Input("act_copy_sql", "n_clicks"),
    prevent_initial_call=True,
)


# ═══════════════════════════════════════════════════════════════════════
# Inline actions: Save to dashboard
# ═══════════════════════════════════════════════════════════════════════


@app.callback(
    Output("inline_save_row", "style"),
    Input("act_save", "n_clicks"),
    State("inline_save_row", "style"),
    prevent_initial_call=True,
)
def toggle_save(n, cur):
    if not n:
        return no_update
    cur = cur or {}
    if cur.get("display") == "none":
        return {"display": "flex"}
    return {"display": "none"}


@app.callback(
    Output("inline_save_msg", "children"),
    Output("inline_save_row", "style", allow_duplicate=True),
    Input("inline_save_btn", "n_clicks"),
    State("inline_save_title", "value"),
    State("chat_sql_store", "data"),
    State("source_selector", "value"),
    State("cust_input", "value"),
    State("whse_input", "value"),
    prevent_initial_call=True,
)
def do_save(n, title, sql, source, cust, whse):
    if not n or not title or len(title) < 3:
        return "Title must be at least 3 characters.", no_update
    try:
        report_service.create(
            title=title, domain=(source or "").upper(),
            sql=sql or "", cust=cust, whse=whse,
        )
        return "Saved to Reports!", {"display": "none"}
    except Exception as exc:
        logger.exception("Save failed")
        return f"Error: {exc}", no_update


# ═══════════════════════════════════════════════════════════════════════
# New Chat
# ═══════════════════════════════════════════════════════════════════════


@app.callback(
    Output("kpi_output_container", "children", allow_duplicate=True),
    Output("chat_history_list", "children", allow_duplicate=True),
    Output("kpi_input", "value", allow_duplicate=True),
    Output("chat_sql_store", "data", allow_duplicate=True),
    Input("new_chat_btn", "n_clicks"),
    State("source_selector", "value"),
    prevent_initial_call=True,
)
def new_chat(n, source):
    if not n:
        return (no_update,) * 4
    dk = (source or "").upper()
    msgs = {
        "LM": "Chat cleared. Ask me about LM KPIs or metrics.",
        "WMS": "Chat cleared. Ask me about WMS metrics.",
        "HR": "Chat cleared. Ask me about HR metrics.",
    }
    return [html.Div(className="cx-spacer"), _sensei(msgs.get(dk, "Chat cleared. Select a source and ask a question."))], [], "", ""



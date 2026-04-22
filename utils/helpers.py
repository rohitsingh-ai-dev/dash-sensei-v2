"""Shared UI helper functions."""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd
import plotly.express as px
from dash import dash_table, dcc, html

logger = logging.getLogger(__name__)


def to_camel_case(text: str) -> str:
    """Convert a string to spaced CamelCase (e.g. 'social circle' → 'Social Circle')."""
    words = re.split(r"[\s_-]+", text.strip())
    cameled = "".join(w.capitalize() for w in words)
    return re.sub(r"(?<!^)(?=[A-Z])", " ", cameled)


def build_data_table(
    data: list[dict[str, Any]],
    table_id: str = "result_table",
    page_size: int = 5,
) -> dash_table.DataTable:
    """Build a styled Dash DataTable from a list of row dicts."""
    if not data:
        return html.Div("No data returned.", className="kpi_output")

    df = pd.DataFrame(data)
    return dash_table.DataTable(
        id=table_id,
        columns=[{"name": col, "id": col} for col in df.columns],
        data=df.to_dict("records"),
        page_size=page_size,
        style_table={"overflowX": "auto"},
        style_header={
            "backgroundColor": "#161b22",
            "color": "#e0e0e0",
            "fontWeight": "600",
            "borderBottom": "1px solid #30363d",
            "fontSize": "12px",
        },
        style_data={
            "backgroundColor": "#0d1117",
            "color": "#c9d1d9",
            "borderBottom": "1px solid #21262d",
            "fontSize": "13px",
        },
        style_cell={
            "textAlign": "left",
            "padding": "8px 12px",
            "border": "none",
            "minWidth": "80px",
        },
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "#111820"},
        ],
        row_selectable=False,
        cell_selectable=False,
    )


def detect_kpi_indicator(results: list[dict]) -> dict | None:
    """Return {label, value, formatted_value} if results represent a single KPI, else None.

    A result is a KPI indicator when it has exactly 1 row with 1-2 columns
    and at least one column is numeric.
    """
    if not results or len(results) != 1:
        return None
    row = results[0]
    cols = list(row.keys())
    if len(cols) > 2:
        return None

    numeric_col = None
    label_col = None
    for c in cols:
        try:
            float(str(row[c]).replace(",", ""))
            numeric_col = c
        except (ValueError, TypeError):
            label_col = c

    if numeric_col is None:
        return None

    val = float(str(row[numeric_col]).replace(",", ""))
    label = str(row.get(label_col, numeric_col)) if label_col else numeric_col
    formatted = f"{val:,.0f}" if val == int(val) else f"{val:,.2f}"
    return {"label": label, "value": val, "formatted_value": formatted}


def auto_detect_chart_type(df: pd.DataFrame) -> dict | None:
    """Heuristic chart selection based on data shape.

    Returns {chart_type, x_col, y_col} or None if no chart makes sense.
    """
    if df.empty or len(df.columns) < 2:
        return None

    rows = len(df)

    # Single row = KPI indicator, handled separately
    if rows == 1:
        return None

    # Find first datetime-like column
    datetime_col = None
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            datetime_col = c
            break
        sample = df[c].dropna().head(5)
        if sample.dtype == object and len(sample) > 0:
            try:
                pd.to_datetime(sample)
                datetime_col = c
                break
            except Exception:
                pass

    # Find numeric columns
    numeric_cols = [
        c for c in df.columns
        if pd.to_numeric(df[c], errors="coerce").notna().sum() > len(df) * 0.5
    ]

    # Find categorical columns
    cat_cols = [c for c in df.columns if c not in numeric_cols and c != datetime_col]

    if not numeric_cols:
        return None

    y_col = numeric_cols[0]

    # Rule 1: datetime x-axis -> Line chart
    if datetime_col:
        return {"chart_type": "Line", "x_col": datetime_col, "y_col": y_col}

    # Rule 2: <= 8 categories -> Pie chart
    if cat_cols and rows <= 8:
        return {"chart_type": "Pie", "x_col": cat_cols[0], "y_col": y_col}

    # Rule 3: <= 30 categories -> Bar chart
    if cat_cols and rows <= 30:
        return {"chart_type": "Bar", "x_col": cat_cols[0], "y_col": y_col}

    # Rule 4: Two numeric columns -> Scatter
    if len(numeric_cols) >= 2:
        return {"chart_type": "Scatter", "x_col": numeric_cols[0], "y_col": numeric_cols[1]}

    # Default: Bar with first cat column
    if cat_cols:
        return {"chart_type": "Bar", "x_col": cat_cols[0], "y_col": y_col}

    return None


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """Safely traverse nested dicts."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


# ═══════════════════════════════════════════════════════════════════════
# Chart builder (shared by Reports tab and Chat result cards)
# ═══════════════════════════════════════════════════════════════════════

GRAPH_CONFIG = {
    "displaylogo": False,
    "toImageButtonOptions": {"format": "png", "scale": 2},
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

CHART_TYPE_OPTIONS = [
    {"label": "Bar", "value": "Bar"},
    {"label": "Line", "value": "Line"},
    {"label": "Pie", "value": "Pie"},
    {"label": "Scatter", "value": "Scatter"},
    {"label": "Area", "value": "Area"},
    {"label": "Funnel", "value": "Funnel"},
]

DARK_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="#333c49",
    plot_bgcolor="#333c49",
    margin=dict(l=40, r=20, t=40, b=40),
)


def _to_float(val):
    try:
        return float(str(val).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def build_chart(
    data: list[dict],
    chart_type: str | None,
    x_col: str | None,
    y_col: str | None,
    chart_title: str | None = None,
    max_rows: int | None = None,
    report_id: str = "",
) -> dcc.Graph | str | None:
    """Build a Plotly figure. Returns dcc.Graph, error string, or None."""
    if not chart_type or not x_col or not y_col or not data:
        return None

    df = pd.DataFrame(data)
    if x_col not in df.columns or y_col not in df.columns:
        return f"Column '{x_col}' or '{y_col}' not found. Available: {list(df.columns)}"

    logger.info(
        "build_chart: x_col=%s y_col=%s y_dtype=%s y_sample=%s",
        x_col, y_col, df[y_col].dtype, df[y_col].head(3).tolist(),
    )

    # Coerce y-axis to numeric
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce").fillna(0)

    # Try to parse x-axis as datetime for better axis formatting
    try:
        df[x_col] = pd.to_datetime(df[x_col])
        df = df.sort_values(x_col).reset_index(drop=True)
    except Exception:
        pass  # leave as-is (string/numeric)

    logger.info(
        "build_chart: after coercion y_dtype=%s y_sample=%s",
        df[y_col].dtype, df[y_col].head(3).tolist(),
    )

    if max_rows:
        df = df.head(max_rows)

    title = chart_title or f"{y_col} by {x_col}"

    try:
        if chart_type == "Bar":
            fig = px.bar(df, x=x_col, y=y_col, title=title)
        elif chart_type == "Line":
            fig = px.line(df, x=x_col, y=y_col, title=title, markers=True)
        elif chart_type == "Pie":
            fig = px.pie(df, names=x_col, values=y_col, title=title)
        elif chart_type == "Scatter":
            fig = px.scatter(df, x=x_col, y=y_col, title=title)
        elif chart_type == "Area":
            fig = px.area(df, x=x_col, y=y_col, title=title)
        elif chart_type == "Funnel":
            fig = px.funnel(df, x=y_col, y=x_col, title=title)
        else:
            return f"Unknown chart type: {chart_type}"

        fig.update_layout(**DARK_LAYOUT)
        return dcc.Graph(
            figure=fig,
            config={**GRAPH_CONFIG, "toImageButtonOptions": {**GRAPH_CONFIG["toImageButtonOptions"], "filename": f"report_{report_id}"}},
            style={"height": "350px"},
        )
    except Exception as exc:
        logger.exception("Chart build failed for report %s", report_id)
        return f"Chart error: {exc}"

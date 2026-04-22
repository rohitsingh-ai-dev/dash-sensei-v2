"""Root application layout — header bar, tab container, splash page, stores."""

from __future__ import annotations

from datetime import datetime

from dash import dcc, html

from layout.splash_page import render_splash_page


def render_main_layout() -> html.Div:
    """Build the top-level DOM skeleton for the entire application."""
    cache_buster = str(datetime.now().timestamp())

    return html.Div(
        children=[
            # ── Header Bar ──────────────────────────────────────────
            html.Div(
                children=[
                    html.Div(
                        html.Img(
                            src=f"assets/sensei2.png?v={cache_buster}",
                            height="50px",
                            className="logoStyle",
                        ),
                        className="logoStyleDiv",
                    ),
                    html.Div(
                        children=[
                            html.Div(
                                "Sensei",
                                id="sensei_title",
                                className="mainTitle",
                            ),
                            html.Div(
                                "Talk to your Data",
                                className="mainTagline",
                            ),
                        ],
                        className="mainTitleTagDiv",
                    ),
                    html.Div(
                        "",
                        id="mainTitleBreadcrumbDiv_home",
                        className="mainTitleBreadcrumbs",
                    ),
                    html.Div(
                        "",
                        id="mainTitleBreadcrumbDiv_kpi",
                        className="mainTitleBreadcrumbs",
                    ),
                    # Health status badge (right-aligned)
                    html.Div(
                        children=[
                            html.Div(
                                id="health_status_badge",
                                children="",
                                style={"fontSize": "80%", "color": "gray"},
                            ),
                        ],
                        id="health_status_div",
                        style={"float": "right", "marginTop": "15px"},
                    ),
                ],
                className="mainHeaderBar",
            ),
            # ── Tab Bar (populated by callbacks) ────────────────────
            html.Div(children=[], id="tabBarParent"),
            # ── Splash Page ─────────────────────────────────────────
            html.Div(
                children=render_splash_page(),
                id="splashPageParent",
            ),
            # ── Client-side stores ──────────────────────────────────
            dcc.Store(id="query_id", storage_type="session", data=None),
            dcc.Store(id="kpi_last_query_sql", storage_type="session", data=None),
            dcc.Store(id="kpi_last_query_df", storage_type="session", data=None),
            dcc.Store(id="session_id", storage_type="session", data=None),
            # ── Persistent interval for query polling (always present) ──
            dcc.Interval(
                id="interval-component",
                interval=4000,
                n_intervals=0,
            ),
            # ── Main content area (populated by tab callbacks) ──────
            html.Div(
                children=[],
                id="main_content",
                className="main_content_styling",
            ),
        ],
        className="overall_main_layout_container",
    )

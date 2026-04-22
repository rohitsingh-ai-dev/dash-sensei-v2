"""Landing / splash page with navigation tiles."""

from __future__ import annotations

from dash import html


def render_splash_page() -> list:
    """Build the landing page shown on initial load."""
    return [
        html.Div(
            "What would you like to ask Sensei today?",
            id="landingPageIntro",
        ),
        html.Div(
            children=[
                # ── Davinci Database tile ───────────────────────────
                html.Div(
                    children=[
                        html.Img(
                            src="assets/database.jpg",
                            className="landingImageStyle",
                        ),
                        html.Div(
                            "Ask Sensei",
                            className="landingImageTitle",
                        ),
                        html.Div(
                            "Query your data with natural language.",
                            className="landingImageDescription",
                        ),
                        html.Div(
                            "Who were my top 5 performers last month?",
                            className="landingImageDescription_itals",
                        ),
                    ],
                    id="selectKPI",
                    className="landingImageStyleContainer",
                ),
                # ── Knowledgebase tile (coming soon) ────────────────
                html.Div(
                    children=[
                        html.Img(
                            src="assets/reference.jpg",
                            className="landingImageStyle",
                            style={"opacity": "0.4"},
                        ),
                        html.Div(
                            "Knowledgebase",
                            className="landingImageTitle",
                        ),
                        html.Div(
                            "Coming Soon",
                            className="landingImageDescription",
                            style={
                                "fontStyle": "italic",
                                "color": "#458e9f",
                                "fontWeight": "bold",
                            },
                        ),
                        html.Div(
                            "Chat with your documentation",
                            className="landingImageDescription_itals",
                        ),
                    ],
                    id="selectKB",
                    className="landingImageStyleContainer",
                    style={"cursor": "default", "pointerEvents": "none"},
                ),
            ],
            id="firstLandingPageTiles",
        ),
        # Placeholder for progress bar (used in KPI tab context)
        html.Div("", id="progress_bar_placeholder"),
    ]

"""UI string constants and question suggestion lists.

Ported from ``dash_sensei/constants.py`` — question lists only.
"""

from __future__ import annotations

# ── LM (Labor Management) Question Suggestions ─────────────────────────
QUESTIONS_LM: list[str] = [
    "Who were my top 5 performers last month?",
    "What was our UPH (units per hour) last week?",
    "Show me efficiency by department for the last 30 days",
    "What is the average performance rating this month?",
    "Which employees had the most indirect hours last week?",
    "Show me headcount by department",
    "What were the total direct hours last month?",
    "Compare UPH between last week and two weeks ago",
    "Who are the bottom 5 performers this month?",
    "Show me overtime hours by employee last week",
]

# ── WMS (Warehouse Management) Question Suggestions ────────────────────
QUESTIONS_WMS: list[str] = [
    "How many orders were shipped last week?",
    "What is the on-time shipment rate this month?",
    "Show me inbound receipt volume by day for the last 7 days",
    "How many orders are currently in backlog?",
    "What were the top 5 SKUs by volume last month?",
    "Show me order accuracy rate for this month",
    "What is the average pick rate per hour?",
    "How many cases were received today?",
    "Show me wave completion rates by day",
    "What is the inventory turnover for the last 30 days?",
]

# ── HR (Human Resources) Question Suggestions ──────────────────────────
QUESTIONS_HR: list[str] = [
    "What is the current headcount by location?",
    "Show me turnover rate for the last 6 months",
    "How many new hires joined this month?",
    "What is the average tenure of employees?",
    "Show me overtime percentage by department",
    "What are the termination reasons for the last quarter?",
    "How many open positions do we have?",
    "Show me attendance rates by location",
    "What is the average hourly rate by department?",
    "How many employees are on leave currently?",
]

# ── Map domain keys to question lists ──────────────────────────────────
QUESTIONS_BY_DOMAIN: dict[str, list[str]] = {
    "LM": QUESTIONS_LM,
    "WMS": QUESTIONS_WMS,
    "HR": QUESTIONS_HR,
}

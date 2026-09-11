"""Streamlit entrypoint for the BIFlow dashboard.

Renders the layout JSON written by DashboardAgent.run() (see agent.py /
layout_builder.py). Reads its path from the DASHBOARD_LAYOUT_PATH env var,
falling back to the default location, so tests can point it at a temp file.
"""

import json
import os

import streamlit as st

from agents.dashboard_agent.agent import DEFAULT_LAYOUT_PATH

SEVERITY_RENDERERS = {
    "critical": st.error,
    "warning": st.warning,
    "info": st.info,
}


def main() -> None:
    """Renders the dashboard application."""
    layout_path = os.environ.get("DASHBOARD_LAYOUT_PATH", DEFAULT_LAYOUT_PATH)

    st.title("BIFlow Dashboard")

    if not os.path.exists(layout_path):
        st.warning("No dashboard data yet — run the pipeline first.")
        return

    with open(layout_path) as f:
        layout = json.load(f)

    for card in layout.get("kpi_cards", []):
        value = card["value"]
        if isinstance(value, float):
            value = round(value, 2)
        st.metric(label=card["label"], value=value)

    insights = layout.get("insights", [])
    if insights:
        st.subheader("Insights")
        for insight in insights:
            render = SEVERITY_RENDERERS.get(insight["severity"], st.info)
            render(f"**{insight['title']}** — {insight['description']}")


if __name__ == "__main__":
    main()

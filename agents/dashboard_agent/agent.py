"""Dashboard Generator Agent entrypoint.

Owns building the interactive dashboard. Called by the Orchestrator with an
AnalysisResult and KPICatalog and returns a DashboardSpec.
"""

import json
import os

from agents.dashboard_agent.layout_builder import build_layout
from shared.schemas.data_contracts import AnalysisResult, AuditReport, DashboardSpec, KPICatalog

DEFAULT_LAYOUT_PATH = "data/processed/dashboard_layout.json"
DEFAULT_DASHBOARD_URL = "http://localhost:3000"


class DashboardAgent:
    """Builds an interactive dashboard from KPIs and analysis insights."""

    # Stores where the layout JSON is written and the URL it's served from.
    def __init__(
        self, layout_path: str = DEFAULT_LAYOUT_PATH, dashboard_url: str = DEFAULT_DASHBOARD_URL
    ) -> None:
        self.layout_path = layout_path
        self.dashboard_url = dashboard_url

    # Builds the layout JSON, writes it to disk, and returns the dashboard spec.
    def run(self, analysis: AnalysisResult, kpis: KPICatalog) -> DashboardSpec:
        """Builds the dashboard layout, writes it for api.py to serve, and returns its spec."""
        layout = build_layout(analysis, kpis)

        os.makedirs(os.path.dirname(self.layout_path) or ".", exist_ok=True)
        with open(self.layout_path, "w") as f:
            json.dump(layout, f, indent=2)

        return DashboardSpec(
            dashboard_url=self.dashboard_url,
            visualizations=["kpi_cards", "insights_panel"],
            kpis_shown=[kpi.name for kpi in kpis.kpis],
        )

    # Adds the Auditor's per-KPI explanations into the already-written layout file.
    def attach_audit_report(self, audit: AuditReport) -> None:
        """Enriches the already-written layout with the Auditor's per-KPI explanations.

        Runs after run(), once the Auditor/XAI agent has produced its report, so the
        dashboard can show *why* a KPI has the value it does without the Dashboard
        Agent needing to depend on the Auditor's output up front.
        """
        with open(self.layout_path) as f:
            layout = json.load(f)

        for card in layout["kpi_cards"]:
            card["explanation"] = audit.explanations.get(card["name"])

        with open(self.layout_path, "w") as f:
            json.dump(layout, f, indent=2)

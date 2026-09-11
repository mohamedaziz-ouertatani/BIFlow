"""Dashboard Generator Agent entrypoint.

Owns building the interactive dashboard. Called by the Orchestrator with an
AnalysisResult and KPICatalog and returns a DashboardSpec.
"""

from agents.dashboard_agent.layout_builder import build_layout
from shared.schemas.data_contracts import AnalysisResult, DashboardSpec, KPICatalog


class DashboardAgent:
    """
    Builds an interactive dashboard from KPIs and analysis insights.

    TODO (owner): implement — decide on Streamlit vs. Dash (see app.py),
    and how visualizations/layout are chosen from the KPI catalog + insights.
    """

    def run(self, analysis: AnalysisResult, kpis: KPICatalog) -> DashboardSpec:
        """Builds the dashboard and returns its spec.

        TODO (owner): implement — call build_layout, render/publish the
        dashboard (app.py), and assemble the DashboardSpec.
        """
        raise NotImplementedError("TODO: implement Dashboard Generator Agent pipeline")

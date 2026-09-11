"""BI Analyst Agent entrypoint.

Owns trend detection, anomaly detection, and insight generation. Called by
the Orchestrator with a KPICatalog and returns an AnalysisResult.
"""

from agents.bi_analyst_agent.insight_generator import generate_insights
from agents.bi_analyst_agent.trend_detection import detect_trends
from shared.schemas.data_contracts import AnalysisResult, KPICatalog


class BIAnalystAgent:
    """Analyzes the KPI catalog to detect trends/anomalies and generate business insights."""

    def run(self, kpis: KPICatalog) -> AnalysisResult:
        """Analyzes the KPI catalog and returns trends + insights."""
        trends = detect_trends(kpis)
        insights = generate_insights(kpis, trends)
        return AnalysisResult(insights=insights, trends=trends)

"""BI Analyst Agent entrypoint.

Owns trend detection, anomaly detection, and insight generation. Called by
the Orchestrator with a CleanedDataset and KPICatalog and returns an
AnalysisResult.
"""

import pandas as pd

from agents.bi_analyst_agent.insight_generator import (
    generate_insights,
    generate_monthly_trend_insights,
)
from agents.bi_analyst_agent.monthly_trends import compute_monthly_trends
from agents.bi_analyst_agent.trend_detection import detect_trends
from shared.schemas.data_contracts import AnalysisResult, CleanedDataset, KPICatalog


class BIAnalystAgent:
    """Analyzes pipeline output to detect trends/anomalies and generate business insights.

    Combines two kinds of trend detection:
    - Threshold evaluation of the single KPICatalog snapshot (trend_detection.py)
    - Real month-over-month trends from the underlying analytical data
      (monthly_trends.py), nested under trends["monthly"] to avoid
      colliding with the threshold-based keys.
    """

    def run(self, cleaned: CleanedDataset, kpis: KPICatalog) -> AnalysisResult:
        """Analyzes the cleaned dataset and KPI catalog, returning trends + insights."""
        threshold_trends = detect_trends(kpis)
        threshold_insights = generate_insights(kpis, threshold_trends)

        analytical_df = pd.read_csv(cleaned.dataset_path)
        monthly_trends = compute_monthly_trends(analytical_df)
        monthly_insights = generate_monthly_trend_insights(monthly_trends)

        trends = {**threshold_trends, "monthly": monthly_trends}
        insights = threshold_insights + monthly_insights

        return AnalysisResult(insights=insights, trends=trends)

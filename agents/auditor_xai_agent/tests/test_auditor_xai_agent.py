"""Tests for the BI Auditor / XAI Agent.

TODO (owner): once implemented, test validate_pipeline_outputs() and
generate_explanations() individually, plus the full agent.run() flow.
"""

import pytest

from agents.auditor_xai_agent.agent import AuditorXAIAgent
from shared.schemas.data_contracts import (
    AnalysisResult,
    CleanedDataset,
    DashboardSpec,
    KPICatalog,
    ProfilingReport,
)


def test_agent_run_not_implemented():
    agent = AuditorXAIAgent()
    cleaned = CleanedDataset(
        dataset_path="data/processed/sample_cleaned.csv",
        data_quality_report=ProfilingReport(
            n_rows=0,
            n_columns=0,
            column_types={},
            missing_values={},
            duplicate_rows=0,
            anomalies=[],
        ),
        transformations_applied=[],
    )
    kpis = KPICatalog(kpis=[], computed_values={})
    analysis = AnalysisResult(insights=[], trends={})
    dashboard = DashboardSpec(dashboard_url="", visualizations=[], kpis_shown=[])
    with pytest.raises(NotImplementedError):
        agent.run(cleaned, kpis, analysis, dashboard)

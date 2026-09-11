"""Tests for the BI Semantic & KPI Agent.

TODO (owner): once implemented, test get_kpi_definitions() per business
domain and the full agent.run() flow against data/sample/.
"""

import pytest

from agents.kpi_semantic_agent.agent import KPISemanticAgent
from shared.schemas.data_contracts import CleanedDataset, ProfilingReport


def test_agent_run_not_implemented():
    agent = KPISemanticAgent()
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
    with pytest.raises(NotImplementedError):
        agent.run(cleaned)

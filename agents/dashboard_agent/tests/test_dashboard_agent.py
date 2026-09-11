"""Tests for the Dashboard Generator Agent.

TODO (owner): once implemented, test build_layout() and the full
agent.run() flow against a sample AnalysisResult + KPICatalog.
"""

import pytest

from agents.dashboard_agent.agent import DashboardAgent
from shared.schemas.data_contracts import AnalysisResult, KPICatalog


def test_agent_run_not_implemented():
    agent = DashboardAgent()
    analysis = AnalysisResult(insights=[], trends={})
    kpis = KPICatalog(kpis=[], computed_values={})
    with pytest.raises(NotImplementedError):
        agent.run(analysis, kpis)

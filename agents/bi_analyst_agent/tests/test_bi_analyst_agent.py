"""Tests for the BI Analyst Agent.

TODO (owner): once implemented, test detect_trends() and generate_insights()
individually, plus the full agent.run() flow against a sample KPICatalog.
"""

import pytest

from agents.bi_analyst_agent.agent import BIAnalystAgent
from shared.schemas.data_contracts import KPICatalog


def test_agent_run_not_implemented():
    agent = BIAnalystAgent()
    kpis = KPICatalog(kpis=[], computed_values={})
    with pytest.raises(NotImplementedError):
        agent.run(kpis)

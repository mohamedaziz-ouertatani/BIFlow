"""Tests for the Data Engineering Agent.

TODO (owner): once implemented, test profile_dataset(), clean_dataset(), and
run_etl() individually against data/sample/, plus the full agent.run() flow.
"""

import pytest

from agents.data_engineering_agent.agent import DataEngineeringAgent
from shared.schemas.data_contracts import RawDatasetRef


def test_agent_run_not_implemented():
    agent = DataEngineeringAgent()
    raw = RawDatasetRef(
        dataset_path="data/sample/sample.csv",
        dataset_name="sample",
        business_domain="e-commerce",
    )
    with pytest.raises(NotImplementedError):
        agent.run(raw)

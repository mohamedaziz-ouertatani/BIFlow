"""Tests for the Data Engineering Agent, run against the real Olist sample data."""

import os

import pandas as pd

from agents.data_engineering_agent.agent import DataEngineeringAgent
from shared.schemas.data_contracts import CleanedDataset, RawDatasetRef

SAMPLE_DIR = "data/sample/olist"


def test_agent_run_produces_cleaned_dataset_from_sample_olist(tmp_path):
    output_path = str(tmp_path / "analytical.csv")
    agent = DataEngineeringAgent(output_path=output_path)
    raw = RawDatasetRef(
        dataset_path=SAMPLE_DIR, dataset_name="olist_ecommerce", business_domain="e-commerce"
    )

    result = agent.run(raw)

    assert isinstance(result, CleanedDataset)
    assert result.dataset_path == output_path
    assert result.data_quality_report.n_rows > 0
    assert len(result.transformations_applied) > 0

    assert os.path.exists(output_path)
    written = pd.read_csv(output_path)
    assert "order_id" in written.columns
    assert "product_category_name_english" in written.columns
    assert len(written) > 0

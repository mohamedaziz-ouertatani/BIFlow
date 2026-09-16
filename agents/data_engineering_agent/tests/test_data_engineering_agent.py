"""Tests for the Data Engineering Agent, run against the real Olist sample data."""

import os

import pandas as pd
import sqlalchemy

from agents.data_engineering_agent.agent import DataEngineeringAgent
from shared.schemas.data_contracts import CleanedDataset, RawDatasetRef

SAMPLE_DIR = "data/sample/olist"
TEST_DATABASE_URL = "postgresql://biflow:biflow@localhost:5433/biflow"


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


def test_agent_run_does_not_touch_postgres_by_default(tmp_path):
    """DataEngineeringAgent() with no database_url must stay CSV-only."""
    output_path = str(tmp_path / "analytical.csv")
    agent = DataEngineeringAgent(output_path=output_path)
    raw = RawDatasetRef(
        dataset_path=SAMPLE_DIR, dataset_name="olist_ecommerce", business_domain="e-commerce"
    )

    result = agent.run(raw)

    assert not any("postgres" in t.lower() for t in result.transformations_applied)


def test_agent_run_loads_into_postgres_when_database_url_given(tmp_path):
    output_path = str(tmp_path / "analytical.csv")
    agent = DataEngineeringAgent(output_path=output_path, database_url=TEST_DATABASE_URL)
    raw = RawDatasetRef(
        dataset_path=SAMPLE_DIR, dataset_name="olist_ecommerce", business_domain="e-commerce"
    )

    result = agent.run(raw)

    assert any("postgres" in t.lower() for t in result.transformations_applied)
    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        count = conn.execute(
            sqlalchemy.text("SELECT COUNT(*) FROM orders_analytical")
        ).scalar()
    assert count > 0


BANKING_SAMPLE_DIR = "data/sample/banking"


def test_agent_run_produces_cleaned_dataset_from_sample_banking(tmp_path):
    output_path = str(tmp_path / "banking_analytical.csv")
    agent = DataEngineeringAgent(output_path=output_path)
    raw = RawDatasetRef(
        dataset_path=BANKING_SAMPLE_DIR, dataset_name="berka_banking", business_domain="banking"
    )

    result = agent.run(raw)

    assert isinstance(result, CleanedDataset)
    assert result.dataset_path == output_path
    assert result.data_quality_report.n_rows > 0
    assert len(result.transformations_applied) > 0

    written = pd.read_csv(output_path)
    assert "trans_id" in written.columns
    assert "region" in written.columns
    assert len(written) > 0

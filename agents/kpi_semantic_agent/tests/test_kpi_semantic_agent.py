"""Tests for the BI Semantic & KPI Agent, run against real Olist sample data."""

import pytest

from agents.data_engineering_agent.agent import DataEngineeringAgent
from agents.kpi_semantic_agent.agent import KPISemanticAgent
from shared.schemas.data_contracts import CleanedDataset, KPICatalog, ProfilingReport, RawDatasetRef

SAMPLE_DIR = "data/sample/olist"


def test_agent_run_computes_kpi_catalog_from_cleaned_dataset(tmp_path):
    analytical_path = str(tmp_path / "analytical.csv")
    raw = RawDatasetRef(
        dataset_path=SAMPLE_DIR, dataset_name="olist_ecommerce", business_domain="e-commerce"
    )
    cleaned = DataEngineeringAgent(output_path=analytical_path).run(raw)

    agent = KPISemanticAgent()
    result = agent.run(cleaned)

    assert isinstance(result, KPICatalog)
    assert {kpi.name for kpi in result.kpis} == {
        "total_revenue",
        "average_order_value",
        "order_count",
        "average_review_score",
        "on_time_delivery_rate",
    }
    # Not all 500 sampled orders have items after cleaning (some order_items
    # rows are dropped for null/negative price), so order_count can be <= 500.
    assert 0 < result.computed_values["order_count"] <= 500
    assert result.computed_values["total_revenue"] > 0


def test_agent_run_uses_business_domain_from_cleaned_dataset_not_a_constructor_default():
    """KPISemanticAgent must read business_domain off CleanedDataset -- there's
    no constructor override, since CleanedDataset now carries it through
    from RawDatasetRef.
    """
    cleaned = CleanedDataset(
        dataset_path="data/sample/olist/does_not_matter.csv",
        data_quality_report=ProfilingReport(
            n_rows=0, n_columns=0, column_types={}, missing_values={}, duplicate_rows=0, anomalies=[]
        ),
        transformations_applied=[],
        business_domain="retail",
    )
    with pytest.raises(KeyError):
        # "retail" has no KPI definitions -- this proves business_domain was
        # actually read from `cleaned`, not defaulted to "e-commerce".
        KPISemanticAgent().run(cleaned)


BANKING_SAMPLE_DIR = "data/sample/banking"


def test_agent_run_computes_banking_kpi_catalog_from_cleaned_dataset(tmp_path):
    analytical_path = str(tmp_path / "banking_analytical.csv")
    raw = RawDatasetRef(
        dataset_path=BANKING_SAMPLE_DIR, dataset_name="berka_banking", business_domain="banking"
    )
    cleaned = DataEngineeringAgent(output_path=analytical_path).run(raw)

    agent = KPISemanticAgent()
    result = agent.run(cleaned)

    assert isinstance(result, KPICatalog)
    assert {kpi.name for kpi in result.kpis} == {
        "total_transaction_volume",
        "average_transaction_value",
        "transaction_count",
        "average_account_balance",
        "loan_good_standing_rate",
    }
    assert result.computed_values["transaction_count"] > 0

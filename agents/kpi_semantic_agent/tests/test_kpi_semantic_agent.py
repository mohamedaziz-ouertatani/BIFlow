"""Tests for the BI Semantic & KPI Agent, run against real Olist sample data."""

from agents.data_engineering_agent.agent import DataEngineeringAgent
from agents.kpi_semantic_agent.agent import KPISemanticAgent
from shared.schemas.data_contracts import KPICatalog, RawDatasetRef

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

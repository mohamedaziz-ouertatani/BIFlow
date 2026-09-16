"""Tests for the BI Analyst Agent, run against the real Olist pipeline output."""

from agents.bi_analyst_agent.agent import BIAnalystAgent
from agents.data_engineering_agent.agent import DataEngineeringAgent
from agents.kpi_semantic_agent.agent import KPISemanticAgent
from shared.schemas.data_contracts import AnalysisResult, RawDatasetRef

SAMPLE_DIR = "data/sample/olist"


def test_agent_run_produces_analysis_result_from_real_kpi_catalog(tmp_path):
    analytical_path = str(tmp_path / "analytical.csv")
    raw = RawDatasetRef(
        dataset_path=SAMPLE_DIR, dataset_name="olist_ecommerce", business_domain="e-commerce"
    )
    cleaned = DataEngineeringAgent(output_path=analytical_path).run(raw)
    kpis = KPISemanticAgent().run(cleaned)

    result = BIAnalystAgent().run(cleaned, kpis)

    assert isinstance(result, AnalysisResult)
    assert result.trends["on_time_delivery_rate"] == {
        "value": kpis.computed_values["on_time_delivery_rate"],
        "threshold": 0.9,
        "status": "healthy"
        if kpis.computed_values["on_time_delivery_rate"] >= 0.9
        else "concerning",
    }
    assert result.trends["average_review_score"] == {
        "value": kpis.computed_values["average_review_score"],
        "threshold": 4.0,
        "status": "healthy"
        if kpis.computed_values["average_review_score"] >= 4.0
        else "concerning",
    }

    # The Olist sample spans many months, so real month-over-month trends
    # should be present too, nested under "monthly" to avoid colliding with
    # the threshold-based keys above.
    assert "monthly" in result.trends
    assert "total_revenue" in result.trends["monthly"]

    threshold_insight_kpis = {"on_time_delivery_rate", "average_review_score"}
    monthly_insight_kpis = set(result.trends["monthly"].keys())
    assert {i.related_kpi for i in result.insights} == threshold_insight_kpis | monthly_insight_kpis


BANKING_SAMPLE_DIR = "data/sample/banking"


def test_agent_run_produces_analysis_result_from_real_banking_kpi_catalog(tmp_path):
    analytical_path = str(tmp_path / "banking_analytical.csv")
    raw = RawDatasetRef(
        dataset_path=BANKING_SAMPLE_DIR, dataset_name="berka_banking", business_domain="banking"
    )
    cleaned = DataEngineeringAgent(output_path=analytical_path).run(raw)
    kpis = KPISemanticAgent().run(cleaned)

    result = BIAnalystAgent().run(cleaned, kpis)

    assert isinstance(result, AnalysisResult)
    assert result.trends["loan_good_standing_rate"] == {
        "value": kpis.computed_values["loan_good_standing_rate"],
        "threshold": 0.85,
        "status": "healthy"
        if kpis.computed_values["loan_good_standing_rate"] >= 0.85
        else "concerning",
    }
    assert "monthly" in result.trends

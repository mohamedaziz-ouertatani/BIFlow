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

    result = BIAnalystAgent().run(kpis)

    assert isinstance(result, AnalysisResult)
    assert result.trends == {
        "on_time_delivery_rate": {
            "value": kpis.computed_values["on_time_delivery_rate"],
            "threshold": 0.9,
            "status": "healthy"
            if kpis.computed_values["on_time_delivery_rate"] >= 0.9
            else "concerning",
        },
        "average_review_score": {
            "value": kpis.computed_values["average_review_score"],
            "threshold": 4.0,
            "status": "healthy"
            if kpis.computed_values["average_review_score"] >= 4.0
            else "concerning",
        },
    }
    assert len(result.insights) == 2
    assert {i.related_kpi for i in result.insights} == {
        "on_time_delivery_rate",
        "average_review_score",
    }

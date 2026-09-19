"""Tests for explainer.py: human-readable explanations for KPIs and insights."""

from agents.auditor_xai_agent.explainer import generate_explanations
from shared.schemas.data_contracts import AnalysisResult, Insight, KPICatalog, KPIDefinition


def test_generate_explanations_includes_formula_and_value_per_kpi():
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="total_revenue",
                formula="sum(price)",
                description="Total revenue",
                dimensions=[],
            )
        ],
        computed_values={"total_revenue": 100.0},
    )
    explanations = generate_explanations(kpis, AnalysisResult(insights=[], trends={}))
    assert "sum(price)" in explanations["total_revenue"]
    assert "100.0" in explanations["total_revenue"]


def test_generate_explanations_includes_insight_description_per_insight():
    analysis = AnalysisResult(
        insights=[
            Insight(
                title="Low review scores",
                description="Average review score is below the 4.0 threshold.",
                related_kpi="average_review_score",
                severity="warning",
            )
        ],
        trends={},
    )
    explanations = generate_explanations(KPICatalog(kpis=[], computed_values={}), analysis)
    assert explanations["Low review scores"] == "Average review score is below the 4.0 threshold."


def test_generate_explanations_rounds_long_float_kpi_values():
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="average_order_value",
                formula="total_revenue / order_count",
                description="AOV",
                dimensions=[],
            )
        ],
        computed_values={"average_order_value": 137.4721818181818},
    )
    explanations = generate_explanations(kpis, AnalysisResult(insights=[], trends={}))
    assert "137.4721818181818" not in explanations["average_order_value"]
    assert "137.47" in explanations["average_order_value"]


def test_generate_explanations_shows_rate_kpi_values_as_percentages():
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="churn_rate",
                formula="count(churn == 'Yes') / count(*)",
                description="Share of customers who have churned.",
                dimensions=[],
            )
        ],
        computed_values={"churn_rate": 0.26537},
    )
    explanations = generate_explanations(kpis, AnalysisResult(insights=[], trends={}))
    assert explanations["churn_rate"].endswith("= 26.5%.")

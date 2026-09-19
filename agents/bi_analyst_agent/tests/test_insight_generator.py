"""Tests for insight_generator.py: turning threshold evaluations into Insight objects."""

from agents.bi_analyst_agent.insight_generator import generate_insights
from shared.schemas.data_contracts import Insight, KPICatalog, KPIDefinition


def _kpi_catalog(**computed_values):
    return KPICatalog(
        kpis=[
            KPIDefinition(name=name, formula="", description="", dimensions=[])
            for name in computed_values
        ],
        computed_values=computed_values,
    )


def test_generate_insights_produces_warning_for_concerning_on_time_delivery_rate():
    kpis = _kpi_catalog(on_time_delivery_rate=0.85)
    trends = {
        "on_time_delivery_rate": {"value": 0.85, "threshold": 0.9, "status": "concerning"}
    }
    insights = generate_insights(kpis, trends)
    assert len(insights) == 1
    insight = insights[0]
    assert isinstance(insight, Insight)
    assert insight.related_kpi == "on_time_delivery_rate"
    assert insight.severity == "warning"
    assert "85%" in insight.description
    assert "0.85" not in insight.description


def test_generate_insights_rounds_long_float_values_in_description():
    kpis = _kpi_catalog(on_time_delivery_rate=0.9385171790235082)
    trends = {
        "on_time_delivery_rate": {
            "value": 0.9385171790235082,
            "threshold": 0.9,
            "status": "healthy",
        }
    }
    insights = generate_insights(kpis, trends)
    assert "0.9385171790235082" not in insights[0].description
    assert "93.9%" in insights[0].description
    assert "90%" in insights[0].description


def test_generate_insights_produces_info_severity_for_healthy_kpi():
    kpis = _kpi_catalog(average_review_score=4.2)
    trends = {"average_review_score": {"value": 4.2, "threshold": 4.0, "status": "healthy"}}
    insights = generate_insights(kpis, trends)
    assert len(insights) == 1
    assert insights[0].severity == "info"
    assert insights[0].related_kpi == "average_review_score"


def test_generate_insights_returns_empty_list_when_no_trends():
    kpis = _kpi_catalog(total_revenue=1000.0)
    insights = generate_insights(kpis, {})
    assert insights == []


def test_generate_insights_produces_named_title_for_concerning_loan_good_standing_rate():
    kpis = _kpi_catalog(loan_good_standing_rate=0.80)
    trends = {
        "loan_good_standing_rate": {"value": 0.80, "threshold": 0.85, "status": "concerning"}
    }
    insights = generate_insights(kpis, trends)
    assert insights[0].title == "Loan default rate above target"


def test_generate_insights_leaves_non_rate_kpi_values_unformatted():
    kpis = _kpi_catalog(average_review_score=4.123)
    trends = {"average_review_score": {"value": 4.123, "threshold": 4.0, "status": "healthy"}}
    insights = generate_insights(kpis, trends)
    assert "4.12" in insights[0].description
    assert "%" not in insights[0].description

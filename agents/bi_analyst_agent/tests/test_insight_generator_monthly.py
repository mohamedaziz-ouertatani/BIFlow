"""Tests for insight_generator.generate_monthly_trend_insights."""

from agents.bi_analyst_agent.insight_generator import generate_monthly_trend_insights
from shared.schemas.data_contracts import Insight


def test_generate_monthly_trend_insights_produces_info_for_increasing_revenue():
    monthly_trends = {
        "total_revenue": {
            "previous_month": "2018-01",
            "latest_month": "2018-02",
            "previous_value": 100.0,
            "latest_value": 150.0,
            "pct_change": 50.0,
            "direction": "increasing",
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert len(insights) == 1
    insight = insights[0]
    assert isinstance(insight, Insight)
    assert insight.related_kpi == "total_revenue"
    assert insight.severity == "info"
    assert "50.0%" in insight.description
    assert "2018-01" in insight.description and "2018-02" in insight.description


def test_generate_monthly_trend_insights_produces_warning_for_decreasing_metric():
    monthly_trends = {
        "average_review_score": {
            "previous_month": "2018-01",
            "latest_month": "2018-02",
            "previous_value": 5.0,
            "latest_value": 2.0,
            "pct_change": -60.0,
            "direction": "decreasing",
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert insights[0].severity == "warning"
    assert insights[0].related_kpi == "average_review_score"


def test_generate_monthly_trend_insights_rounds_long_float_values():
    monthly_trends = {
        "average_review_score": {
            "previous_month": "2018-07",
            "latest_month": "2018-08",
            "previous_value": 4.290322580645161,
            "latest_value": 4.294117647058823,
            "pct_change": 0.09,
            "direction": "increasing",
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert "4.290322580645161" not in insights[0].description
    assert "4.29" in insights[0].description


def test_generate_monthly_trend_insights_produces_critical_for_anomaly():
    monthly_trends = {
        "total_revenue": {
            "previous_month": "2018-04",
            "latest_month": "2018-05",
            "previous_value": 100.0,
            "latest_value": 500.0,
            "pct_change": 400.0,
            "direction": "increasing",
            "is_anomaly": True,
            "z_score": 3.27,
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert insights[0].severity == "critical"
    assert "3.27" in insights[0].description


def test_generate_monthly_trend_insights_non_anomaly_keeps_normal_severity():
    monthly_trends = {
        "total_revenue": {
            "previous_month": "2018-01",
            "latest_month": "2018-02",
            "previous_value": 100.0,
            "latest_value": 150.0,
            "pct_change": 50.0,
            "direction": "increasing",
            "is_anomaly": False,
            "z_score": None,
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert insights[0].severity == "info"


def test_generate_monthly_trend_insights_uses_named_label_for_transaction_volume():
    monthly_trends = {
        "total_transaction_volume": {
            "previous_month": "2018-01",
            "latest_month": "2018-02",
            "previous_value": 100.0,
            "latest_value": 150.0,
            "pct_change": 50.0,
            "direction": "increasing",
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert insights[0].title == "Transaction volume increasing month-over-month"


def test_generate_monthly_trend_insights_sets_month_to_the_latest_month():
    monthly_trends = {
        "total_revenue": {
            "previous_month": "2018-01",
            "latest_month": "2018-02",
            "previous_value": 100.0,
            "latest_value": 150.0,
            "pct_change": 50.0,
            "direction": "increasing",
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert insights[0].month == "2018-02"


def test_generate_monthly_trend_insights_explains_empty_trends_for_telco():
    insights = generate_monthly_trend_insights({}, "telco")
    assert len(insights) == 1
    assert insights[0].severity == "info"
    assert insights[0].title == "No month-over-month trends available"
    assert "telco" in insights[0].description


def test_generate_monthly_trend_insights_stays_empty_for_domains_with_a_time_dimension():
    """An empty trends dict for e-commerce/banking means "not enough history
    yet", not "no time dimension" -- shouldn't get the telco-style note."""
    insights = generate_monthly_trend_insights({}, "e-commerce")
    assert insights == []


def test_generate_monthly_trend_insights_stays_empty_when_domain_not_given():
    insights = generate_monthly_trend_insights({})
    assert insights == []

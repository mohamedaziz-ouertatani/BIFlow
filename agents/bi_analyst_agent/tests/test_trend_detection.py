"""Tests for trend_detection.py: threshold-based evaluation of KPI values."""

from agents.bi_analyst_agent.trend_detection import detect_trends
from shared.schemas.data_contracts import KPICatalog, KPIDefinition


def _kpi_catalog(**computed_values):
    return KPICatalog(
        kpis=[
            KPIDefinition(name=name, formula="", description="", dimensions=[])
            for name in computed_values
        ],
        computed_values=computed_values,
    )


def test_detect_trends_flags_on_time_delivery_rate_below_threshold_as_concerning():
    kpis = _kpi_catalog(on_time_delivery_rate=0.85)
    trends = detect_trends(kpis)
    assert trends["on_time_delivery_rate"] == {
        "value": 0.85,
        "threshold": 0.9,
        "status": "concerning",
    }


def test_detect_trends_flags_average_review_score_at_or_above_threshold_as_healthy():
    kpis = _kpi_catalog(average_review_score=4.2)
    trends = detect_trends(kpis)
    assert trends["average_review_score"] == {
        "value": 4.2,
        "threshold": 4.0,
        "status": "healthy",
    }


def test_detect_trends_only_evaluates_kpis_with_a_known_threshold():
    kpis = _kpi_catalog(total_revenue=1000.0)
    trends = detect_trends(kpis)
    assert trends == {}


def test_detect_trends_flags_loan_good_standing_rate_below_threshold_as_concerning():
    kpis = _kpi_catalog(loan_good_standing_rate=0.80)
    trends = detect_trends(kpis)
    assert trends["loan_good_standing_rate"] == {
        "value": 0.80,
        "threshold": 0.85,
        "status": "concerning",
    }


def test_detect_trends_flags_average_account_balance_at_or_above_threshold_as_healthy():
    kpis = _kpi_catalog(average_account_balance=35000.0)
    trends = detect_trends(kpis)
    assert trends["average_account_balance"] == {
        "value": 35000.0,
        "threshold": 30000.0,
        "status": "healthy",
    }

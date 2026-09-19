"""Tests for metrics.py: which KPIs are rates and how they're formatted."""

from shared.metrics import PERCENT_METRICS, format_percent


def test_percent_metrics_are_exactly_the_rate_kpis():
    assert PERCENT_METRICS == {"on_time_delivery_rate", "loan_good_standing_rate", "churn_rate"}


def test_format_percent_uses_one_decimal_and_drops_a_trailing_zero():
    assert format_percent(0.93851) == "93.9%"
    assert format_percent(0.9) == "90%"
    assert format_percent(1.0) == "100%"
    assert format_percent(0.0) == "0%"

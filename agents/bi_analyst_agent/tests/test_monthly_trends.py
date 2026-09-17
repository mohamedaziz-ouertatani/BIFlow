"""Tests for monthly_trends.py: real month-over-month trend detection."""

import pandas as pd

from agents.bi_analyst_agent.monthly_trends import compute_monthly_trends


def test_compute_monthly_trends_detects_increasing_revenue():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-05", "2018-01-10", "2018-02-05"]
            ),
            "order_status": ["delivered", "delivered", "delivered"],
            "price": [50.0, 50.0, 150.0],
            "review_score": [5, 4, 5],
        }
    )
    trends = compute_monthly_trends(df, "e-commerce")
    assert trends["total_revenue"] == {
        "previous_month": "2018-01",
        "latest_month": "2018-02",
        "previous_value": 100.0,
        "latest_value": 150.0,
        "pct_change": 50.0,
        "direction": "increasing",
        "series": [
            {"month": "2018-01", "value": 100.0},
            {"month": "2018-02", "value": 150.0},
        ],
        "is_anomaly": False,
        "z_score": None,
    }


def test_compute_monthly_trends_includes_full_series_for_charting():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-05", "2018-02-05", "2018-03-05"]
            ),
            "order_status": ["delivered", "delivered", "delivered"],
            "price": [50.0, 100.0, 150.0],
            "review_score": [5, 4, 3],
        }
    )
    trends = compute_monthly_trends(df, "e-commerce")
    assert trends["total_revenue"]["series"] == [
        {"month": "2018-01", "value": 50.0},
        {"month": "2018-02", "value": 100.0},
        {"month": "2018-03", "value": 150.0},
    ]


def test_compute_monthly_trends_detects_decreasing_review_score():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2"],
            "order_purchase_timestamp": pd.to_datetime(["2018-01-05", "2018-02-05"]),
            "order_status": ["delivered", "delivered"],
            "price": [50.0, 50.0],
            "review_score": [5, 2],
        }
    )
    trends = compute_monthly_trends(df, "e-commerce")
    assert trends["average_review_score"]["direction"] == "decreasing"
    assert trends["average_review_score"]["previous_value"] == 5.0
    assert trends["average_review_score"]["latest_value"] == 2.0


def test_compute_monthly_trends_counts_distinct_orders_per_month_not_items():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o1", "o2"],
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-05", "2018-01-05", "2018-02-05"]
            ),
            "order_status": ["delivered", "delivered", "delivered"],
            "price": [10.0, 20.0, 30.0],
            "review_score": [5, 5, 4],
        }
    )
    trends = compute_monthly_trends(df, "e-commerce")
    assert trends["order_count"]["previous_value"] == 1.0
    assert trends["order_count"]["latest_value"] == 1.0


def test_compute_monthly_trends_excludes_trailing_near_empty_month():
    """A trailing month with a handful of stray orders (e.g. 1 order after
    thousands) shouldn't be treated as "the latest month" -- it makes any
    trend look like a total collapse when it's really just incomplete data.
    """
    jan_orders = [f"o{i}" for i in range(10)]
    feb_orders = [f"p{i}" for i in range(10)]
    order_ids = jan_orders + feb_orders + ["stray"]
    dates = (
        ["2018-01-05"] * 10 + ["2018-02-05"] * 10 + ["2018-03-01"]
    )
    df = pd.DataFrame(
        {
            "order_id": order_ids,
            "order_purchase_timestamp": pd.to_datetime(dates),
            "order_status": ["delivered"] * 21,
            "price": [10.0] * 21,
            "review_score": [5] * 21,
        }
    )
    trends = compute_monthly_trends(df, "e-commerce")
    assert trends["order_count"]["previous_month"] == "2018-01"
    assert trends["order_count"]["latest_month"] == "2018-02"
    assert trends["order_count"]["latest_value"] == 10.0


def test_compute_monthly_trends_omits_metrics_with_fewer_than_two_months():
    df = pd.DataFrame(
        {
            "order_id": ["o1"],
            "order_purchase_timestamp": pd.to_datetime(["2018-01-05"]),
            "order_status": ["delivered"],
            "price": [50.0],
            "review_score": [5],
        }
    )
    trends = compute_monthly_trends(df, "e-commerce")
    assert trends == {}


def test_compute_monthly_trends_banking_detects_increasing_transaction_volume():
    df = pd.DataFrame(
        {
            "trans_id": [1, 2, 3],
            "date": pd.to_datetime(["2018-01-05", "2018-01-10", "2018-02-05"]),
            "type": ["PRIJEM", "PRIJEM", "PRIJEM"],
            "amount": [50.0, 50.0, 150.0],
            "balance": [500.0, 550.0, 700.0],
        }
    )
    trends = compute_monthly_trends(df, "banking")
    assert trends["total_transaction_volume"] == {
        "previous_month": "2018-01",
        "latest_month": "2018-02",
        "previous_value": 100.0,
        "latest_value": 150.0,
        "pct_change": 50.0,
        "direction": "increasing",
        "series": [
            {"month": "2018-01", "value": 100.0},
            {"month": "2018-02", "value": 150.0},
        ],
        "is_anomaly": False,
        "z_score": None,
    }


def test_compute_monthly_trends_banking_counts_distinct_transactions_per_month():
    df = pd.DataFrame(
        {
            "trans_id": [1, 2, 3],
            "date": pd.to_datetime(["2018-01-05", "2018-01-06", "2018-02-05"]),
            "type": ["PRIJEM", "VYDAJ", "PRIJEM"],
            "amount": [50.0, 20.0, 30.0],
            "balance": [500.0, 480.0, 510.0],
        }
    )
    trends = compute_monthly_trends(df, "banking")
    assert trends["transaction_count"]["previous_value"] == 2.0
    assert trends["transaction_count"]["latest_value"] == 1.0


def test_compute_monthly_trends_banking_averages_balance_per_month():
    df = pd.DataFrame(
        {
            "trans_id": [1, 2, 3],
            "date": pd.to_datetime(["2018-01-05", "2018-01-06", "2018-02-05"]),
            "type": ["PRIJEM", "PRIJEM", "PRIJEM"],
            "amount": [50.0, 50.0, 50.0],
            "balance": [400.0, 600.0, 900.0],
        }
    )
    trends = compute_monthly_trends(df, "banking")
    assert trends["average_account_balance"]["previous_value"] == 500.0
    assert trends["average_account_balance"]["latest_value"] == 900.0


def test_compute_monthly_trends_flags_anomaly_far_outside_historical_range():
    """4 stable months followed by a month that spikes far outside the
    historical range should be flagged as an anomaly with a z-score."""
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3", "o4", "o5"],
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-05", "2018-02-05", "2018-03-05", "2018-04-05", "2018-05-05"]
            ),
            "order_status": ["delivered"] * 5,
            "price": [100.0, 105.0, 95.0, 100.0, 500.0],
            "review_score": [5, 5, 5, 5, 5],
        }
    )
    trends = compute_monthly_trends(df, "e-commerce")
    revenue_trend = trends["total_revenue"]
    assert revenue_trend["is_anomaly"] is True
    assert revenue_trend["z_score"] is not None
    assert abs(revenue_trend["z_score"]) > 2


def test_compute_monthly_trends_no_anomaly_with_insufficient_history():
    """Fewer than 3 prior months isn't enough to judge normal variance, so
    the latest month should never be flagged regardless of its value."""
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-05", "2018-02-05", "2018-03-05"]
            ),
            "order_status": ["delivered"] * 3,
            "price": [100.0, 100.0, 900.0],
            "review_score": [5, 5, 5],
        }
    )
    trends = compute_monthly_trends(df, "e-commerce")
    revenue_trend = trends["total_revenue"]
    assert revenue_trend["is_anomaly"] is False
    assert revenue_trend["z_score"] is None


def test_compute_monthly_trends_banking_omits_metrics_with_fewer_than_two_months():
    df = pd.DataFrame(
        {
            "trans_id": [1],
            "date": pd.to_datetime(["2018-01-05"]),
            "type": ["PRIJEM"],
            "amount": [50.0],
            "balance": [500.0],
        }
    )
    trends = compute_monthly_trends(df, "banking")
    assert trends == {}


def test_compute_monthly_trends_telco_always_returns_empty():
    """Telco has no transaction dates -- only static per-customer tenure --
    so there's no time dimension to bucket by."""
    df = pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "tenure": [1, 34],
            "monthly_charges": [29.85, 56.95],
            "churn": ["Yes", "No"],
        }
    )
    trends = compute_monthly_trends(df, "telco")
    assert trends == {}

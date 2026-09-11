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
    trends = compute_monthly_trends(df)
    assert trends["total_revenue"] == {
        "previous_month": "2018-01",
        "latest_month": "2018-02",
        "previous_value": 100.0,
        "latest_value": 150.0,
        "pct_change": 50.0,
        "direction": "increasing",
    }


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
    trends = compute_monthly_trends(df)
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
    trends = compute_monthly_trends(df)
    assert trends["order_count"]["previous_value"] == 1.0
    assert trends["order_count"]["latest_value"] == 1.0


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
    trends = compute_monthly_trends(df)
    assert trends == {}

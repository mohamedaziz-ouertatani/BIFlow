"""Tests for kpi_computation.py: computing KPI values from the analytical table."""

import pandas as pd

from agents.kpi_semantic_agent.kpi_computation import compute_kpis


def test_compute_kpis_total_revenue_excludes_canceled_orders():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "order_status": ["delivered", "delivered", "canceled"],
            "price": [100.0, 50.0, 999.0],
            "review_score": [5, 4, None],
            "order_delivered_customer_date": [None, None, None],
            "order_estimated_delivery_date": [None, None, None],
        }
    )
    computed = compute_kpis(df, "e-commerce")
    assert computed["total_revenue"] == 150.0


def test_compute_kpis_order_count_counts_all_distinct_orders_regardless_of_status():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o1", "o2", "o3"],
            "order_status": ["delivered", "delivered", "delivered", "canceled"],
            "price": [10.0, 20.0, 50.0, 999.0],
            "review_score": [5, 5, 4, None],
            "order_delivered_customer_date": [None, None, None, None],
            "order_estimated_delivery_date": [None, None, None, None],
        }
    )
    computed = compute_kpis(df, "e-commerce")
    assert computed["order_count"] == 3


def test_compute_kpis_average_order_value_divides_revenue_by_non_canceled_order_count():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "order_status": ["delivered", "delivered", "canceled"],
            "price": [100.0, 50.0, 999.0],
            "review_score": [5, 4, None],
            "order_delivered_customer_date": [None, None, None],
            "order_estimated_delivery_date": [None, None, None],
        }
    )
    computed = compute_kpis(df, "e-commerce")
    assert computed["average_order_value"] == 75.0


def test_compute_kpis_average_review_score_ignores_missing_reviews():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "order_status": ["delivered", "delivered", "delivered"],
            "price": [10.0, 20.0, 30.0],
            "review_score": [4, None, 2],
            "order_delivered_customer_date": [None, None, None],
            "order_estimated_delivery_date": [None, None, None],
        }
    )
    computed = compute_kpis(df, "e-commerce")
    assert computed["average_review_score"] == 3.0


def test_compute_kpis_on_time_delivery_rate_over_delivered_orders_only():
    df = pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3", "o4"],
            "order_status": ["delivered", "delivered", "delivered", "shipped"],
            "price": [10.0, 20.0, 30.0, 40.0],
            "review_score": [5, 5, 5, 5],
            "order_delivered_customer_date": pd.to_datetime(
                ["2018-01-05", "2018-01-15", None, None]
            ),
            "order_estimated_delivery_date": pd.to_datetime(
                ["2018-01-10", "2018-01-10", "2018-01-10", "2018-01-10"]
            ),
        }
    )
    computed = compute_kpis(df, "e-commerce")
    # only o1 and o2 were delivered; o1 on time, o2 late -> 1/2 = 0.5
    assert computed["on_time_delivery_rate"] == 0.5


def _banking_df(**overrides):
    base = pd.DataFrame(
        {
            "trans_id": [1, 2, 3, 4],
            "type": ["PRIJEM", "PRIJEM", "VYDAJ", "VYDAJ"],
            "amount": [500.0, 300.0, 100.0, 50.0],
            "balance": [1000.0, 1300.0, 1200.0, 1150.0],
            "loan_status": ["C", "C", "C", "C"],
        }
    )
    return base.assign(**overrides) if overrides else base


def test_compute_kpis_banking_total_transaction_volume_sums_credits_only():
    computed = compute_kpis(_banking_df(), "banking")
    assert computed["total_transaction_volume"] == 800.0


def test_compute_kpis_banking_transaction_count_counts_all_transaction_types():
    computed = compute_kpis(_banking_df(), "banking")
    assert computed["transaction_count"] == 4


def test_compute_kpis_banking_average_transaction_value_divides_volume_by_credit_count():
    computed = compute_kpis(_banking_df(), "banking")
    assert computed["average_transaction_value"] == 400.0


def test_compute_kpis_banking_average_account_balance_means_balance_column():
    computed = compute_kpis(_banking_df(), "banking")
    assert computed["average_account_balance"] == 1162.5


def test_compute_kpis_banking_loan_good_standing_rate_counts_a_and_c_as_good():
    df = _banking_df(loan_status=["A", "B", "C", "D"])
    computed = compute_kpis(df, "banking")
    assert computed["loan_good_standing_rate"] == 0.5


def test_compute_kpis_banking_loan_good_standing_rate_is_none_when_no_loan():
    df = _banking_df(loan_status=[None, None, None, None])
    computed = compute_kpis(df, "banking")
    assert computed["loan_good_standing_rate"] is None

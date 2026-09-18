"""Tests for row_filters.py: the row-level filter behind each KPI."""

import pandas as pd
import pytest

from agents.kpi_semantic_agent.row_filters import filter_rows


def _ecommerce_df():
    return pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "order_status": ["delivered", "delivered", "canceled"],
            "price": [100.0, 50.0, 999.0],
            "review_score": [5, None, 4],
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-05", "2018-02-05", "2018-02-10"]
            ),
            "order_delivered_customer_date": pd.to_datetime(
                ["2018-01-10", None, "2018-02-15"]
            ),
            "order_estimated_delivery_date": pd.to_datetime(
                ["2018-01-12", "2018-02-08", "2018-02-12"]
            ),
        }
    )


def test_filter_rows_ecommerce_total_revenue_excludes_canceled():
    result = filter_rows(_ecommerce_df(), "e-commerce", "total_revenue")
    assert list(result["order_id"]) == ["o1", "o2"]


def test_filter_rows_ecommerce_order_count_has_no_filter():
    result = filter_rows(_ecommerce_df(), "e-commerce", "order_count")
    assert len(result) == 3


def test_filter_rows_ecommerce_average_review_score_drops_missing_reviews():
    result = filter_rows(_ecommerce_df(), "e-commerce", "average_review_score")
    assert list(result["order_id"]) == ["o1", "o3"]


def test_filter_rows_ecommerce_on_time_delivery_rate_keeps_delivered_only():
    result = filter_rows(_ecommerce_df(), "e-commerce", "on_time_delivery_rate")
    assert list(result["order_id"]) == ["o1", "o3"]


def test_filter_rows_ecommerce_scopes_to_a_month():
    result = filter_rows(_ecommerce_df(), "e-commerce", "order_count", month="2018-02")
    assert list(result["order_id"]) == ["o2", "o3"]


def test_filter_rows_unknown_kpi_raises_keyerror():
    with pytest.raises(KeyError):
        filter_rows(_ecommerce_df(), "e-commerce", "not_a_real_kpi")


def test_filter_rows_unknown_domain_raises_keyerror():
    with pytest.raises(KeyError):
        filter_rows(_ecommerce_df(), "not_a_real_domain", "total_revenue")


def _banking_df():
    return pd.DataFrame(
        {
            "trans_id": [1, 2, 3, 4],
            "type": ["PRIJEM", "PRIJEM", "VYDAJ", "VYDAJ"],
            "amount": [500.0, 300.0, 100.0, 50.0],
            "balance": [1000.0, None, 1200.0, 1150.0],
            "loan_status": ["C", "C", None, "C"],
            "date": pd.to_datetime(["2018-01-05", "2018-02-05", "2018-02-06", "2018-02-07"]),
        }
    )


def test_filter_rows_banking_total_transaction_volume_keeps_credits_only():
    result = filter_rows(_banking_df(), "banking", "total_transaction_volume")
    assert list(result["trans_id"]) == [1, 2]


def test_filter_rows_banking_average_account_balance_drops_missing_balance():
    result = filter_rows(_banking_df(), "banking", "average_account_balance")
    assert list(result["trans_id"]) == [1, 3, 4]


def test_filter_rows_banking_loan_good_standing_rate_keeps_rows_with_a_loan():
    result = filter_rows(_banking_df(), "banking", "loan_good_standing_rate")
    assert list(result["trans_id"]) == [1, 2, 4]


def test_filter_rows_banking_scopes_to_a_month():
    result = filter_rows(_banking_df(), "banking", "transaction_count", month="2018-02")
    assert list(result["trans_id"]) == [2, 3, 4]


def _telco_df():
    return pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "churn": ["Yes", "No"],
            "monthly_charges": [29.85, 56.95],
            "tenure": [1, 34],
        }
    )


def test_filter_rows_telco_kpis_have_no_filter():
    for kpi_name in (
        "churn_rate",
        "average_monthly_charges",
        "average_tenure_months",
        "total_customers",
    ):
        result = filter_rows(_telco_df(), "telco", kpi_name)
        assert len(result) == 2


def test_filter_rows_telco_ignores_month_since_there_is_no_date_column():
    result = filter_rows(_telco_df(), "telco", "total_customers", month="2018-02")
    assert len(result) == 2

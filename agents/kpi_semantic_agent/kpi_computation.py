"""Computes KPI values from the analytical table, per business domain."""

from typing import Any

import pandas as pd


def compute_kpis(df: pd.DataFrame, business_domain: str) -> dict[str, Any]:
    """Computes the KPI values for business_domain from the analytical table."""
    if business_domain == "e-commerce":
        return _compute_ecommerce_kpis(df)
    if business_domain == "banking":
        return _compute_banking_kpis(df)
    raise KeyError(business_domain)


def _compute_ecommerce_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the e-commerce KPI values from the order-item-level analytical table."""
    non_canceled = df[df["order_status"] != "canceled"]
    total_revenue = float(non_canceled["price"].sum())
    order_count = int(df["order_id"].nunique())
    non_canceled_order_count = int(non_canceled["order_id"].nunique())
    average_order_value = (
        total_revenue / non_canceled_order_count if non_canceled_order_count else 0.0
    )

    average_review_score = float(df["review_score"].mean())

    delivered = df[df["order_delivered_customer_date"].notna()]
    on_time_delivery_rate = (
        float(
            (
                delivered["order_delivered_customer_date"]
                <= delivered["order_estimated_delivery_date"]
            ).mean()
        )
        if len(delivered)
        else None
    )

    return {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "average_order_value": average_order_value,
        "average_review_score": average_review_score,
        "on_time_delivery_rate": on_time_delivery_rate,
    }


def _compute_banking_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the banking KPI values from the transaction-level analytical table."""
    credits = df[df["type"] == "PRIJEM"]
    total_transaction_volume = float(credits["amount"].sum())
    transaction_count = int(df["trans_id"].nunique())
    credit_transaction_count = int(credits["trans_id"].nunique())
    average_transaction_value = (
        total_transaction_volume / credit_transaction_count if credit_transaction_count else 0.0
    )

    average_account_balance = float(df["balance"].mean())

    with_loan = df[df["loan_status"].notna()]
    loan_good_standing_rate = (
        float(with_loan["loan_status"].isin(["A", "C"]).mean()) if len(with_loan) else None
    )

    return {
        "total_transaction_volume": total_transaction_volume,
        "average_transaction_value": average_transaction_value,
        "transaction_count": transaction_count,
        "average_account_balance": average_account_balance,
        "loan_good_standing_rate": loan_good_standing_rate,
    }

"""Computes KPI values from the analytical table, per business domain."""

from typing import Any

import pandas as pd

from agents.kpi_semantic_agent.row_filters import filter_rows


# Computes every KPI's value per distinct value of the given breakdown dimension.
def compute_kpi_breakdowns(
    df: pd.DataFrame, dimension_column: str, business_domain: str
) -> dict[str, dict[str, Any]]:
    """Computes every KPI's value per distinct value of `dimension_column`.

    Applies the same formulas as `compute_kpis` to each group's subset of
    rows. Since the analytical table is at order-item grain, an order
    spanning multiple categories is attributed to each — consistent with how
    `total_revenue`/`order_count` are computed overall, but worth knowing
    when reading a category breakdown.
    """
    return {
        # str(): these become JSON object keys, which must be strings.
        str(value): compute_kpis(group, business_domain)
        for value, group in df.dropna(subset=[dimension_column]).groupby(dimension_column)
    }


# Dispatches to the domain-specific KPI computation.
def compute_kpis(df: pd.DataFrame, business_domain: str) -> dict[str, Any]:
    """Computes the KPI values for business_domain from the analytical table."""
    if business_domain == "e-commerce":
        return _compute_ecommerce_kpis(df)
    if business_domain == "banking":
        return _compute_banking_kpis(df)
    if business_domain == "telco":
        return _compute_telco_kpis(df)
    raise KeyError(business_domain)


# Computes the e-commerce KPI values from the order-item-level analytical table.
def _compute_ecommerce_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the e-commerce KPI values from the order-item-level analytical table."""
    # The table is at ORDER-ITEM grain (one row per item): revenue is the sum of item prices, but
    # counting orders needs nunique on order_id, since an order with 3 items spans 3 rows.
    non_canceled = filter_rows(df, "e-commerce", "total_revenue")
    total_revenue = float(non_canceled["price"].sum())
    order_count = int(df["order_id"].nunique())
    non_canceled_order_count = int(non_canceled["order_id"].nunique())
    average_order_value = (
        total_revenue / non_canceled_order_count if non_canceled_order_count else 0.0
    )

    # Mean over item rows, so an order with several items counts once per item. (The monthly trend
    # in monthly_trends.py collapses to one row per order first, so the two can differ slightly.)
    reviewed = filter_rows(df, "e-commerce", "average_review_score")
    average_review_score = float(reviewed["review_score"].mean())

    # `delivered <= estimated` gives a True/False Series; the mean of booleans is the share of True,
    # i.e. the on-time rate as a 0-1 fraction. None when nothing has been delivered (no NaN).
    delivered = filter_rows(df, "e-commerce", "on_time_delivery_rate")
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


# Computes the banking KPI values from the transaction-level analytical table.
def _compute_banking_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the banking KPI values from the transaction-level analytical table."""
    # Volume and average transaction value only count credits (PRIJEM = money coming in).
    credits = filter_rows(df, "banking", "total_transaction_volume")
    total_transaction_volume = float(credits["amount"].sum())
    transaction_count = int(df["trans_id"].nunique())
    credit_transaction_count = int(credits["trans_id"].nunique())
    average_transaction_value = (
        total_transaction_volume / credit_transaction_count if credit_transaction_count else 0.0
    )

    # `balance` is the account's running balance after each transaction, so this is an average
    # over transactions, not over accounts.
    balance_rows = filter_rows(df, "banking", "average_account_balance")
    average_account_balance = float(balance_rows["balance"].mean())

    # loan_status was joined onto every transaction row, so this rate is taken over the
    # transaction rows of accounts that have a loan (accounts with more transactions weigh more),
    # not over distinct loans. A and C = good standing (finished OK / running OK).
    with_loan = filter_rows(df, "banking", "loan_good_standing_rate")
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


# Computes the telco KPI values from the customer-level analytical table.
def _compute_telco_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the telco KPI values from the customer-level analytical table."""
    total_customers = int(len(df))
    # `churn` holds the strings Yes/No: comparing to 'Yes' gives booleans, whose mean is the churn share.
    churn_rate = (
        float((df["churn"] == "Yes").mean()) if total_customers else None
    )
    average_monthly_charges = float(df["monthly_charges"].mean())
    average_tenure_months = float(df["tenure"].mean())

    return {
        "churn_rate": churn_rate,
        "average_monthly_charges": average_monthly_charges,
        "average_tenure_months": average_tenure_months,
        "total_customers": total_customers,
    }

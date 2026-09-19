"""Real month-over-month trend detection from the analytical table, per
business domain.

Unlike trend_detection.py (which only evaluates a single KPICatalog
snapshot against fixed thresholds), this buckets the underlying analytical
data by calendar month and compares the last two complete months with data.
"""

from typing import Any

import pandas as pd


# Classifies a month-over-month change as increasing, decreasing, or flat.
def _direction(latest: float, previous: float) -> str:
    if latest > previous:
        return "increasing"
    if latest < previous:
        return "decreasing"
    return "flat"


MIN_HISTORY_FOR_ANOMALY = 3
ANOMALY_Z_SCORE_THRESHOLD = 2.0


# Flags the latest month as anomalous if it's far outside the range of prior months.
def _detect_anomaly(series: pd.Series) -> tuple[bool, float | None]:
    """Computes a z-score for the latest value against the mean/stdev of
    prior months. Needs at least MIN_HISTORY_FOR_ANOMALY prior points --
    with fewer, there isn't enough history to know what's normal."""
    history = series.iloc[:-1]
    if len(history) < MIN_HISTORY_FOR_ANOMALY:
        return False, None
    std = float(history.std(ddof=0))
    # A perfectly flat history has std 0, which would divide by zero: treat it as 'no anomaly'.
    if std == 0:
        return False, None
    # z-score = how many standard deviations the latest month sits from the average of the earlier
    # months (ddof=0 -> population std). |z| > 2 is flagged: roughly the outer 5% for bell-shaped data.
    z_score = (float(series.iloc[-1]) - float(history.mean())) / std
    return abs(z_score) > ANOMALY_Z_SCORE_THRESHOLD, round(z_score, 2)


# Builds a trend entry from the last two months of a monthly series.
def _trend_entry(series: pd.Series) -> dict[str, Any] | None:
    """Builds a trend entry from the last two months of a monthly series."""
    if len(series) < 2:
        return None
    # Trends compare only the last two months of the (already 'complete') series.
    previous_month, latest_month = series.index[-2], series.index[-1]
    previous_value, latest_value = float(series.iloc[-2]), float(series.iloc[-1])
    # Percent change vs the previous month; 0.0 if the previous value is 0 (avoids dividing by zero).
    pct_change = (
        (latest_value - previous_value) / previous_value * 100 if previous_value else 0.0
    )
    is_anomaly, z_score = _detect_anomaly(series)
    return {
        "previous_month": previous_month,
        "latest_month": latest_month,
        "previous_value": previous_value,
        "latest_value": latest_value,
        "pct_change": round(pct_change, 2),
        "direction": _direction(latest_value, previous_value),
        "series": [
            {"month": month, "value": float(value)} for month, value in series.items()
        ],
        "is_anomaly": is_anomaly,
        "z_score": z_score,
    }


MIN_ORDER_COUNT_RATIO = 0.2


# Excludes trailing months with unusually low row counts from the trend series.
def _complete_months(count_by_month: pd.Series) -> pd.Index:
    """Excludes trailing months whose row count is far below typical volume
    (e.g. a handful of stray rows after the data effectively ends) --
    otherwise they get treated as "the latest month" and produce a
    misleading near-total-collapse trend.
    """
    if count_by_month.empty:
        return count_by_month.index
    # A month is 'complete' if it has at least 20% of the busiest month's rows. This also drops
    # sparse months at the start of the data, not only stray trailing ones.
    threshold = count_by_month.max() * MIN_ORDER_COUNT_RATIO
    return count_by_month[count_by_month >= threshold].index


# Dispatches to the domain-specific monthly trend computation.
def compute_monthly_trends(analytical_df: pd.DataFrame, business_domain: str) -> dict[str, Any]:
    """Computes month-over-month trends for business_domain from the analytical table."""
    if business_domain == "e-commerce":
        return _compute_ecommerce_monthly_trends(analytical_df)
    if business_domain == "banking":
        return _compute_banking_monthly_trends(analytical_df)
    if business_domain == "telco":
        return _compute_telco_monthly_trends(analytical_df)
    raise KeyError(business_domain)


# Computes month-over-month trends for revenue, order count, and review score.
def _compute_ecommerce_monthly_trends(analytical_df: pd.DataFrame) -> dict[str, Any]:
    """Computes month-over-month trends for revenue, order count, and review score."""
    df = analytical_df.copy()
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    # 'YYYY-MM' text label: sorts chronologically and matches the drill-down's month filter.
    df["month"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m")

    # One row per order: the table has one row per item, so counting orders or averaging review
    # scores per month must collapse to order level first (else multi-item orders count many times).
    # Revenue below is different: `price` is per item, so it sums the item rows directly.
    orders_level = df[["order_id", "month", "review_score"]].drop_duplicates(subset="order_id")

    non_canceled = df[df["order_status"] != "canceled"]
    revenue_by_month = non_canceled.groupby("month")["price"].sum().sort_index()
    order_count_by_month = orders_level.groupby("month")["order_id"].nunique().sort_index()
    review_score_by_month = orders_level.groupby("month")["review_score"].mean().sort_index()

    # Keep only complete months and align all three series to them, so an incomplete month
    # disappears from every trend at once.
    complete_months = _complete_months(order_count_by_month)
    revenue_by_month = revenue_by_month.reindex(complete_months)
    order_count_by_month = order_count_by_month.reindex(complete_months)
    review_score_by_month = review_score_by_month.reindex(complete_months)

    trends = {}
    for name, series in (
        ("total_revenue", revenue_by_month),
        ("order_count", order_count_by_month),
        ("average_review_score", review_score_by_month),
    ):
        entry = _trend_entry(series)
        if entry is not None:
            trends[name] = entry

    return trends


# Always empty: telco has no transaction dates, only static per-customer tenure.
def _compute_telco_monthly_trends(analytical_df: pd.DataFrame) -> dict[str, Any]:
    """Always returns {} -- the telco analytical table has no time dimension
    to bucket by (only a static 'tenure in months' field per customer, not
    calendar dates), so there is no real month-over-month series to compute.
    """
    return {}


# Computes month-over-month trends for transaction volume, count, and balance.
def _compute_banking_monthly_trends(analytical_df: pd.DataFrame) -> dict[str, Any]:
    """Computes month-over-month trends for transaction volume, count, and balance."""
    df = analytical_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")

    credits = df[df["type"] == "PRIJEM"]
    volume_by_month = credits.groupby("month")["amount"].sum().sort_index()
    transaction_count_by_month = df.groupby("month")["trans_id"].nunique().sort_index()
    balance_by_month = df.groupby("month")["balance"].mean().sort_index()

    complete_months = _complete_months(transaction_count_by_month)
    volume_by_month = volume_by_month.reindex(complete_months)
    transaction_count_by_month = transaction_count_by_month.reindex(complete_months)
    balance_by_month = balance_by_month.reindex(complete_months)

    trends = {}
    for name, series in (
        ("total_transaction_volume", volume_by_month),
        ("transaction_count", transaction_count_by_month),
        ("average_account_balance", balance_by_month),
    ):
        entry = _trend_entry(series)
        if entry is not None:
            trends[name] = entry

    return trends

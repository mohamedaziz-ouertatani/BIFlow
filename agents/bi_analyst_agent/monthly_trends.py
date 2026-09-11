"""Real month-over-month trend detection from the analytical order-item table.

Unlike trend_detection.py (which only evaluates a single KPICatalog
snapshot against fixed thresholds), this buckets the underlying analytical
data by calendar month and compares the last two complete months with data.
"""

from typing import Any

import pandas as pd


def _direction(latest: float, previous: float) -> str:
    if latest > previous:
        return "increasing"
    if latest < previous:
        return "decreasing"
    return "flat"


def _trend_entry(series: pd.Series) -> dict[str, Any] | None:
    """Builds a trend entry from the last two months of a monthly series."""
    if len(series) < 2:
        return None
    previous_month, latest_month = series.index[-2], series.index[-1]
    previous_value, latest_value = float(series.iloc[-2]), float(series.iloc[-1])
    pct_change = (
        (latest_value - previous_value) / previous_value * 100 if previous_value else 0.0
    )
    return {
        "previous_month": previous_month,
        "latest_month": latest_month,
        "previous_value": previous_value,
        "latest_value": latest_value,
        "pct_change": round(pct_change, 2),
        "direction": _direction(latest_value, previous_value),
    }


def compute_monthly_trends(analytical_df: pd.DataFrame) -> dict[str, Any]:
    """Computes month-over-month trends for revenue, order count, and review score."""
    df = analytical_df.copy()
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["month"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m")

    orders_level = df[["order_id", "month", "review_score"]].drop_duplicates(subset="order_id")

    non_canceled = df[df["order_status"] != "canceled"]
    revenue_by_month = non_canceled.groupby("month")["price"].sum().sort_index()
    order_count_by_month = orders_level.groupby("month")["order_id"].nunique().sort_index()
    review_score_by_month = orders_level.groupby("month")["review_score"].mean().sort_index()

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

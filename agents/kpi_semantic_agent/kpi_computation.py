"""Computes KPI values from the analytical order-item table."""

from typing import Any

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
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

"""KPI definitions for the business domain(s) BIFlow supports."""

from shared.schemas.data_contracts import KPIDefinition

_ECOMMERCE_KPIS = [
    KPIDefinition(
        name="total_revenue",
        formula="sum(price) where order_status != 'canceled'",
        description="Total revenue from non-canceled order items.",
        dimensions=[],
    ),
    KPIDefinition(
        name="average_order_value",
        formula="total_revenue / count(distinct order_id where order_status != 'canceled')",
        description="Average amount spent per non-canceled order.",
        dimensions=[],
    ),
    KPIDefinition(
        name="order_count",
        formula="count(distinct order_id)",
        description="Total number of distinct orders, across all statuses.",
        dimensions=[],
    ),
    KPIDefinition(
        name="average_review_score",
        formula="mean(review_score)",
        description="Average customer review score (1-5) across orders with a review.",
        dimensions=[],
    ),
    KPIDefinition(
        name="on_time_delivery_rate",
        formula=(
            "count(order_delivered_customer_date <= order_estimated_delivery_date) "
            "/ count(order_delivered_customer_date is not null)"
        ),
        description="Share of delivered orders that arrived on or before the estimated date.",
        dimensions=[],
    ),
]

_KPIS_BY_DOMAIN = {
    "e-commerce": _ECOMMERCE_KPIS,
}


def get_kpi_definitions(business_domain: str) -> list[KPIDefinition]:
    """Returns the list of KPI definitions relevant to the given business domain."""
    return _KPIS_BY_DOMAIN[business_domain]

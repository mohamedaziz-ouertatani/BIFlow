"""KPI definitions for the business domain(s) BIFlow supports."""

from shared.schemas.data_contracts import KPIDefinition

# Dimensions every e-commerce KPI can be broken down by (see kpi_computation.py
# DIMENSION_COLUMNS for the analytical-table column each maps to).
_BREAKDOWN_DIMENSIONS = ["category", "state"]

_ECOMMERCE_KPIS = [
    KPIDefinition(
        name="total_revenue",
        formula="sum(price) where order_status != 'canceled'",
        description="Total revenue from non-canceled order items.",
        dimensions=_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="average_order_value",
        formula="total_revenue / count(distinct order_id where order_status != 'canceled')",
        description="Average amount spent per non-canceled order.",
        dimensions=_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="order_count",
        formula="count(distinct order_id)",
        description="Total number of distinct orders, across all statuses.",
        dimensions=_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="average_review_score",
        formula="mean(review_score)",
        description="Average customer review score (1-5) across orders with a review.",
        dimensions=_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="on_time_delivery_rate",
        formula=(
            "count(order_delivered_customer_date <= order_estimated_delivery_date) "
            "/ count(order_delivered_customer_date is not null)"
        ),
        description="Share of delivered orders that arrived on or before the estimated date.",
        dimensions=_BREAKDOWN_DIMENSIONS,
    ),
]

_BANKING_KPIS = [
    KPIDefinition(
        name="total_transaction_volume",
        formula="sum(amount) where type == 'PRIJEM'",
        description="Total value of credit transactions.",
        dimensions=[],
    ),
    KPIDefinition(
        name="average_transaction_value",
        formula="total_transaction_volume / count(distinct trans_id where type == 'PRIJEM')",
        description="Average value of a credit transaction.",
        dimensions=[],
    ),
    KPIDefinition(
        name="transaction_count",
        formula="count(distinct trans_id)",
        description="Total number of transactions, both credits and debits.",
        dimensions=[],
    ),
    KPIDefinition(
        name="average_account_balance",
        formula="mean(balance)",
        description="Average account balance across all transactions.",
        dimensions=[],
    ),
    KPIDefinition(
        name="loan_good_standing_rate",
        formula="count(loan_status in ('A','C')) / count(loan_status is not null)",
        description="Share of loans that are in good standing (finished without issue, or running normally).",
        dimensions=[],
    ),
]

_KPIS_BY_DOMAIN = {
    "e-commerce": _ECOMMERCE_KPIS,
    "banking": _BANKING_KPIS,
}


# Returns the list of KPI definitions relevant to the given business domain.
def get_kpi_definitions(business_domain: str) -> list[KPIDefinition]:
    """Returns the list of KPI definitions relevant to the given business domain."""
    return _KPIS_BY_DOMAIN[business_domain]

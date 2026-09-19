"""KPI definitions for the business domain(s) BIFlow supports."""

from shared.schemas.data_contracts import KPIDefinition

# Dimensions every e-commerce KPI can be broken down by (see agent.py
# DIMENSION_COLUMNS_BY_DOMAIN for the analytical-table column each maps to).
_BREAKDOWN_DIMENSIONS = ["category", "state"]

# `formula` is display text only: it's shown in the dashboard and the Auditor's explanations but
# never executed. The real math is in kpi_computation.py, the row selection in row_filters.py.
_ECOMMERCE_KPIS = [
    KPIDefinition(
        name="total_revenue",
        formula="sum(price) where order_status != 'canceled'",
        description="Total revenue from non-canceled order items.",
        dimensions=_BREAKDOWN_DIMENSIONS,
        additive=True,
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
        additive=True,
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

_REGION_BREAKDOWN = ["region"]

_BANKING_KPIS = [
    KPIDefinition(
        name="total_transaction_volume",
        formula="sum(amount) where type == 'PRIJEM'",
        description="Total value of credit transactions.",
        dimensions=_REGION_BREAKDOWN,
        additive=True,
    ),
    KPIDefinition(
        name="average_transaction_value",
        formula="total_transaction_volume / count(distinct trans_id where type == 'PRIJEM')",
        description="Average value of a credit transaction.",
        dimensions=_REGION_BREAKDOWN,
    ),
    KPIDefinition(
        name="transaction_count",
        formula="count(distinct trans_id)",
        description="Total number of transactions, both credits and debits.",
        dimensions=_REGION_BREAKDOWN,
        additive=True,
    ),
    KPIDefinition(
        name="average_account_balance",
        formula="mean(balance)",
        description="Average account balance across all transactions.",
        dimensions=_REGION_BREAKDOWN,
    ),
    KPIDefinition(
        name="loan_good_standing_rate",
        formula="count(loan_status in ('A','C')) / count(loan_status is not null)",
        description="Share of loans that are in good standing (finished without issue, or running normally).",
        dimensions=_REGION_BREAKDOWN,
    ),
]

_TELCO_BREAKDOWN_DIMENSIONS = ["contract", "internet_service"]

_TELCO_KPIS = [
    KPIDefinition(
        name="churn_rate",
        formula="count(churn == 'Yes') / count(*)",
        description="Share of customers who have churned.",
        dimensions=_TELCO_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="average_monthly_charges",
        formula="mean(monthly_charges)",
        description="Average amount billed to a customer per month.",
        dimensions=_TELCO_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="average_tenure_months",
        formula="mean(tenure)",
        description="Average number of months a customer has stayed with the company.",
        dimensions=_TELCO_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="total_customers",
        formula="count(*)",
        description="Total number of customers.",
        dimensions=_TELCO_BREAKDOWN_DIMENSIONS,
        additive=True,
    ),
]

_KPIS_BY_DOMAIN = {
    "e-commerce": _ECOMMERCE_KPIS,
    "banking": _BANKING_KPIS,
    "telco": _TELCO_KPIS,
}


# Returns the list of KPI definitions relevant to the given business domain.
def get_kpi_definitions(business_domain: str) -> list[KPIDefinition]:
    """Returns the list of KPI definitions relevant to the given business domain."""
    return _KPIS_BY_DOMAIN[business_domain]

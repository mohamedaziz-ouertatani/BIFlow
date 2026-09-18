"""Insight generation logic for the BI Analyst Agent."""

from typing import Any

from shared.schemas.data_contracts import Insight, KPICatalog

TITLES = {
    ("on_time_delivery_rate", "healthy"): "Strong on-time delivery",
    ("on_time_delivery_rate", "concerning"): "On-time delivery rate below target",
    ("average_review_score", "healthy"): "Strong customer satisfaction",
    ("average_review_score", "concerning"): "Review scores below target",
    ("loan_good_standing_rate", "healthy"): "Strong loan repayment performance",
    ("loan_good_standing_rate", "concerning"): "Loan default rate above target",
    ("average_account_balance", "healthy"): "Healthy average account balance",
    ("average_account_balance", "concerning"): "Average account balance below target",
}

SEVERITY_BY_STATUS = {
    "healthy": "info",
    "concerning": "warning",
}


# Converts each threshold evaluation (healthy/concerning) into a human-readable Insight.
def generate_insights(kpis: KPICatalog, trends: dict[str, Any]) -> list[Insight]:
    """Turns each threshold evaluation in trends into a human-readable Insight."""
    insights = []
    for kpi_name, evaluation in trends.items():
        status = evaluation["status"]
        title = TITLES.get((kpi_name, status), f"{kpi_name}: {status}")
        value = round(evaluation["value"], 2)
        threshold = round(evaluation["threshold"], 2)
        description = (
            f"{kpi_name} is {value} "
            f"({'at or above' if status == 'healthy' else 'below'} "
            f"the {threshold} threshold)."
        )
        insights.append(
            Insight(
                title=title,
                description=description,
                related_kpi=kpi_name,
                severity=SEVERITY_BY_STATUS.get(status, "info"),
            )
        )
    return insights


MONTHLY_TREND_LABELS = {
    "total_revenue": "Revenue",
    "order_count": "Order volume",
    "average_review_score": "Review score",
    "total_transaction_volume": "Transaction volume",
    "transaction_count": "Transaction count",
    "average_account_balance": "Account balance",
}

SEVERITY_BY_DIRECTION = {
    "increasing": "info",
    "flat": "info",
    "decreasing": "warning",
}

# Domains whose analytical table has no calendar date to bucket by, so
# compute_monthly_trends always returns {} for them -- surfaced as an info
# insight rather than left as a silent gap.
NO_TIME_DIMENSION_DOMAINS = {"telco"}


# Converts each month-over-month trend into a human-readable Insight.
def generate_monthly_trend_insights(
    monthly_trends: dict[str, Any], business_domain: str | None = None
) -> list[Insight]:
    """Turns each real month-over-month trend into a human-readable Insight.

    If monthly_trends is empty because business_domain has no time
    dimension to bucket by, returns one explanatory info Insight instead of
    silently producing nothing.
    """
    if not monthly_trends and business_domain in NO_TIME_DIMENSION_DOMAINS:
        return [
            Insight(
                title="No month-over-month trends available",
                description=(
                    f"The '{business_domain}' dataset has no transaction dates -- only "
                    "a static per-customer tenure -- so there is no calendar time "
                    "series to compute month-over-month trends from."
                ),
                related_kpi="",
                severity="info",
            )
        ]

    insights = []
    for metric_name, trend in monthly_trends.items():
        label = MONTHLY_TREND_LABELS.get(metric_name, metric_name)
        title = f"{label} {trend['direction']} month-over-month"
        previous_value = round(trend["previous_value"], 2)
        latest_value = round(trend["latest_value"], 2)
        description = (
            f"{label} went from {previous_value} in {trend['previous_month']} "
            f"to {latest_value} in {trend['latest_month']} "
            f"({trend['pct_change']:+.1f}%)."
        )
        is_anomaly = trend.get("is_anomaly", False)
        if is_anomaly:
            description += (
                f" This is unusual: {trend['z_score']} standard deviations from "
                "the typical range for this metric."
            )
            severity = "critical"
        else:
            severity = SEVERITY_BY_DIRECTION.get(trend["direction"], "info")
        insights.append(
            Insight(
                title=title,
                description=description,
                related_kpi=metric_name,
                severity=severity,
                month=trend["latest_month"],
            )
        )
    return insights

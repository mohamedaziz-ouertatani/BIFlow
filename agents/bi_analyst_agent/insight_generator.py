"""Insight generation logic for the BI Analyst Agent."""

from typing import Any

from shared.schemas.data_contracts import Insight, KPICatalog

TITLES = {
    ("on_time_delivery_rate", "healthy"): "Strong on-time delivery",
    ("on_time_delivery_rate", "concerning"): "On-time delivery rate below target",
    ("average_review_score", "healthy"): "Strong customer satisfaction",
    ("average_review_score", "concerning"): "Review scores below target",
}

SEVERITY_BY_STATUS = {
    "healthy": "info",
    "concerning": "warning",
}


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

"""Dashboard layout construction logic."""

from typing import Any

from shared.schemas.data_contracts import AnalysisResult, KPICatalog


_COMPARISON_FIELDS = (
    "previous_month",
    "latest_month",
    "previous_value",
    "latest_value",
    "pct_change",
    "direction",
)


def build_layout(analysis: AnalysisResult, kpis: KPICatalog) -> dict[str, Any]:
    """Builds a JSON-serializable dashboard layout spec (KPI cards + insights panel)."""
    monthly = analysis.trends.get("monthly", {})

    kpi_cards = [
        {
            "name": kpi.name,
            "label": kpi.description,
            "value": kpis.computed_values.get(kpi.name),
            "comparison": (
                {field: monthly[kpi.name][field] for field in _COMPARISON_FIELDS}
                if kpi.name in monthly
                else None
            ),
        }
        for kpi in kpis.kpis
    ]

    insights = [
        {
            "title": insight.title,
            "description": insight.description,
            "related_kpi": insight.related_kpi,
            "severity": insight.severity,
        }
        for insight in analysis.insights
    ]

    monthly_trends = {
        metric: trend["series"]
        for metric, trend in analysis.trends.get("monthly", {}).items()
    }

    return {
        "kpi_cards": kpi_cards,
        "insights": insights,
        "monthly_trends": monthly_trends,
    }

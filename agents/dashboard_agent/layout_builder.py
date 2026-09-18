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

_MAX_BREAKDOWN_ITEMS = 8


# Builds one {kpi_name}_by_{dimension} -> sorted [{label, value}] entry per
# KPI/dimension pair that has breakdown data, capping long tails into "Other".
def _build_category_breakdowns(kpis: KPICatalog) -> dict[str, list[dict[str, Any]]]:
    """Builds the category breakdown series for every dimensioned KPI that has data."""
    result: dict[str, list[dict[str, Any]]] = {}
    for kpi in kpis.kpis:
        for dimension in kpi.dimensions:
            groups = kpis.breakdowns.get(dimension, {})
            points = [
                {"label": label, "value": values[kpi.name]}
                for label, values in groups.items()
                if values.get(kpi.name) is not None
            ]
            if not points:
                continue
            points.sort(key=lambda p: p["value"], reverse=True)
            if len(points) > _MAX_BREAKDOWN_ITEMS:
                head = points[: _MAX_BREAKDOWN_ITEMS - 1]
                other_value = sum(p["value"] for p in points[_MAX_BREAKDOWN_ITEMS - 1 :])
                points = head + [{"label": "Other", "value": other_value}]
            result[f"{kpi.name}_by_{dimension}"] = points
    return result


# Assembles the JSON dashboard payload: KPI cards, insights, and monthly trend series.
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
            "month": insight.month,
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
        "category_breakdowns": _build_category_breakdowns(kpis),
        "business_domain": kpis.business_domain,
    }

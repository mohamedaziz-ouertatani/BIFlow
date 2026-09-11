"""Dashboard layout construction logic."""

from typing import Any

from shared.schemas.data_contracts import AnalysisResult, KPICatalog


def build_layout(analysis: AnalysisResult, kpis: KPICatalog) -> dict[str, Any]:
    """Builds a JSON-serializable dashboard layout spec (KPI cards + insights panel)."""
    kpi_cards = [
        {
            "name": kpi.name,
            "label": kpi.description,
            "value": kpis.computed_values.get(kpi.name),
        }
        for kpi in kpis.kpis
    ]

    insights = [
        {
            "title": insight.title,
            "description": insight.description,
            "severity": insight.severity,
        }
        for insight in analysis.insights
    ]

    return {
        "kpi_cards": kpi_cards,
        "insights": insights,
    }

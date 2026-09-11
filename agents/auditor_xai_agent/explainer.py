"""Explainability (XAI) logic for the Auditor/XAI Agent."""

from shared.schemas.data_contracts import AnalysisResult, KPICatalog


def generate_explanations(kpis: KPICatalog, analysis: AnalysisResult) -> dict[str, str]:
    """Generates human-readable explanations for KPIs and insights."""
    explanations = {}

    for kpi in kpis.kpis:
        value = kpis.computed_values.get(kpi.name)
        if isinstance(value, float):
            value = round(value, 2)
        explanations[kpi.name] = (
            f"{kpi.description} Computed as `{kpi.formula}` = {value}."
        )

    for insight in analysis.insights:
        explanations[insight.title] = insight.description

    return explanations

"""Explainability (XAI) logic for the Auditor/XAI Agent."""

from shared.metrics import PERCENT_METRICS, format_percent
from shared.schemas.data_contracts import AnalysisResult, KPICatalog


# Builds a human-readable explanation string for every KPI and insight.
def generate_explanations(kpis: KPICatalog, analysis: AnalysisResult) -> dict[str, str]:
    """Generates human-readable explanations for KPIs and insights."""
    explanations = {}

    for kpi in kpis.kpis:
        value = kpis.computed_values.get(kpi.name)
        # Rates are shown as percentages and other floats rounded to 2 decimals;
        # None (no data) and ints pass through unchanged.
        if kpi.name in PERCENT_METRICS and isinstance(value, float):
            value = format_percent(value)
        elif isinstance(value, float):
            value = round(value, 2)
        explanations[kpi.name] = (
            f"{kpi.description} Computed as `{kpi.formula}` = {value}."
        )

    for insight in analysis.insights:
        explanations[insight.title] = insight.description

    return explanations

"""Explainability (XAI) logic for the Auditor/XAI Agent."""

from shared.schemas.data_contracts import AnalysisResult, KPICatalog


def generate_explanations(kpis: KPICatalog, analysis: AnalysisResult) -> dict[str, str]:
    """Generates human-readable explanations for KPIs and insights.

    TODO (owner): implement — e.g. explain how each KPI was computed, why an
    insight was flagged with its given severity. Return a dict mapping a
    subject (KPI name or insight title) to its explanation, for
    AuditReport.explanations. See docs/xai_report_template.md.
    """
    raise NotImplementedError("TODO: implement explanation generation")

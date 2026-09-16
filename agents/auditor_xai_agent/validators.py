"""Validation logic for the Auditor/XAI Agent."""

from shared.schemas.data_contracts import AnalysisResult, CleanedDataset, KPICatalog

WARNING_SEVERITIES = {"warning", "critical"}


# Checks data quality and insight severities to derive an overall pass/warn/fail status.
def validate_pipeline_outputs(
    cleaned: CleanedDataset, kpis: KPICatalog, analysis: AnalysisResult
) -> str:
    """Validates outputs across the pipeline and returns a validation_status."""
    if cleaned.data_quality_report.n_rows == 0:
        return "failed"

    has_data_quality_anomalies = bool(cleaned.data_quality_report.anomalies)
    has_concerning_insights = any(
        insight.severity in WARNING_SEVERITIES for insight in analysis.insights
    )
    if has_data_quality_anomalies or has_concerning_insights:
        return "passed_with_warnings"

    return "passed"

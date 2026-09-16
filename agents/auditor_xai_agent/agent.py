"""BI Auditor / XAI Agent entrypoint.

Owns validation, explanations, and traceability. Called by the Orchestrator
with the outputs of every prior stage and returns the final AuditReport.
"""

from agents.auditor_xai_agent.explainer import generate_explanations
from agents.auditor_xai_agent.validators import validate_pipeline_outputs
from shared.schemas.data_contracts import (
    AnalysisResult,
    AuditReport,
    CleanedDataset,
    DashboardSpec,
    KPICatalog,
)


class AuditorXAIAgent:
    """Validates pipeline outputs and produces explanations + a traceability log."""

    # Validates the run, generates explanations, and builds the final audit report.
    def run(
        self,
        cleaned: CleanedDataset,
        kpis: KPICatalog,
        analysis: AnalysisResult,
        dashboard: DashboardSpec,
    ) -> AuditReport:
        """Validates the pipeline run and returns the final audit report."""
        validation_status = validate_pipeline_outputs(cleaned, kpis, analysis)
        explanations = generate_explanations(kpis, analysis)

        traceability_log = [
            f"data_engineering: produced {cleaned.dataset_path} "
            f"({cleaned.data_quality_report.n_rows} rows profiled, "
            f"{len(cleaned.transformations_applied)} transformations applied)",
            f"kpi_semantic: computed {len(kpis.kpis)} KPIs",
            f"bi_analyst: generated {len(analysis.insights)} insights",
            f"dashboard: published to {dashboard.dashboard_url} "
            f"({len(dashboard.visualizations)} visualizations)",
        ]

        return AuditReport(
            validation_status=validation_status,
            explanations=explanations,
            traceability_log=traceability_log,
        )

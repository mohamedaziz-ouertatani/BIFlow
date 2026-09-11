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
    """
    Validates pipeline outputs and produces explanations + a traceability
    log for the full BIFlow run.

    TODO (owner): implement validation rules (e.g. data quality thresholds,
    KPI sanity checks) and explanation generation (e.g. why an insight was
    flagged, how a KPI was computed).
    """

    def run(
        self,
        cleaned: CleanedDataset,
        kpis: KPICatalog,
        analysis: AnalysisResult,
        dashboard: DashboardSpec,
    ) -> AuditReport:
        """Validates the pipeline run and returns the final audit report.

        TODO (owner): implement — call validate_pipeline_outputs, then
        generate_explanations, and assemble the AuditReport using the
        Orchestrator's execution trace.
        """
        raise NotImplementedError("TODO: implement Auditor/XAI Agent pipeline")

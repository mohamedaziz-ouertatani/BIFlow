"""BIFlow Orchestrator.

Coordinates the pipeline across all agents. Agents never call each other
directly — every hand-off passes through this class.
"""

import uuid

from agents.auditor_xai_agent.agent import AuditorXAIAgent
from agents.bi_analyst_agent.agent import BIAnalystAgent
from agents.dashboard_agent.agent import DEFAULT_LAYOUT_PATH, DashboardAgent
from agents.data_engineering_agent.agent import DEFAULT_OUTPUT_PATH, DataEngineeringAgent
from agents.kpi_semantic_agent.agent import KPISemanticAgent
from orchestrator.execution_log import ExecutionLogger
from shared.schemas.data_contracts import (
    AnalysisResult,
    AuditReport,
    CleanedDataset,
    DashboardSpec,
    KPICatalog,
    RawDatasetRef,
)


class PipelineStageError(Exception):
    """Raised when a pipeline stage fails, halting the run.

    Wraps the original exception (available via `__cause__`/`raise ... from`)
    and names the stage that failed, so callers (CLI, API, tests) can report
    a clear error instead of a bare traceback from deep inside an agent.
    """

    def __init__(self, stage: str, original: Exception) -> None:
        self.stage = stage
        super().__init__(f"Pipeline halted: stage '{stage}' failed: {original}")


class BIFlowOrchestrator:
    """Coordinates the BIFlow pipeline across all agents.

    Stage failures halt the pipeline immediately (no retry, no skip — each
    stage's output feeds the next, so there is nothing meaningful to retry
    or skip to) and are re-raised as `PipelineStageError` naming the stage
    that failed.

    Each run's step-by-step trace (start/success/failure per stage) is
    recorded in-memory via `execution_log.ExecutionLogger` and left on
    `self.execution_log` after `run_pipeline` returns (or raises), for
    callers that want tracing beyond the `AuditReport.traceability_log`
    the Auditor/XAI agent synthesizes from each stage's own output.
    """

    def __init__(
        self,
        analytical_path: str = DEFAULT_OUTPUT_PATH,
        dashboard_layout_path: str = DEFAULT_LAYOUT_PATH,
        database_url: str | None = None,
    ) -> None:
        self.analytical_path = analytical_path
        self.dashboard_layout_path = dashboard_layout_path
        self.database_url = database_url
        self.execution_log: ExecutionLogger | None = None

    def run_pipeline(self, raw_dataset: RawDatasetRef) -> AuditReport:
        """Runs the full pipeline end-to-end and returns the final audit report.

        Raises `PipelineStageError` if any stage fails.
        """
        self.execution_log = ExecutionLogger(run_id=str(uuid.uuid4()))

        cleaned = self._run_stage("data_engineering", self._run_data_engineering, raw_dataset)
        kpis = self._run_stage("kpi_semantic", self._run_kpi_semantic, cleaned)
        analysis = self._run_stage("bi_analyst", self._run_bi_analyst, cleaned, kpis)
        dashboard_agent = DashboardAgent(layout_path=self.dashboard_layout_path)
        dashboard = self._run_stage("dashboard", dashboard_agent.run, analysis, kpis)
        audit = self._run_stage(
            "auditor", self._run_auditor, cleaned, kpis, analysis, dashboard
        )
        dashboard_agent.attach_audit_report(audit)
        return audit

    def _run_stage(self, stage: str, fn, *args):
        self.execution_log.log(stage, "started")
        try:
            result = fn(*args)
        except Exception as exc:
            self.execution_log.log(stage, "failed", details={"error": str(exc)})
            raise PipelineStageError(stage, exc) from exc
        self.execution_log.log(stage, "succeeded")
        return result

    def _run_data_engineering(self, raw_dataset: RawDatasetRef) -> CleanedDataset:
        return DataEngineeringAgent(
            output_path=self.analytical_path, database_url=self.database_url
        ).run(raw_dataset)

    def _run_kpi_semantic(self, cleaned: CleanedDataset) -> KPICatalog:
        return KPISemanticAgent().run(cleaned)

    def _run_bi_analyst(self, cleaned: CleanedDataset, kpis: KPICatalog) -> AnalysisResult:
        return BIAnalystAgent().run(cleaned, kpis)

    def _run_auditor(
        self,
        cleaned: CleanedDataset,
        kpis: KPICatalog,
        analysis: AnalysisResult,
        dashboard: DashboardSpec,
    ) -> AuditReport:
        return AuditorXAIAgent().run(cleaned, kpis, analysis, dashboard)

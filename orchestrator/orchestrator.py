"""BIFlow Orchestrator.

Coordinates the pipeline across all agents. Agents never call each other
directly — every hand-off passes through this class.
"""

from agents.auditor_xai_agent.agent import AuditorXAIAgent
from agents.bi_analyst_agent.agent import BIAnalystAgent
from agents.dashboard_agent.agent import DEFAULT_LAYOUT_PATH, DashboardAgent
from agents.data_engineering_agent.agent import DEFAULT_OUTPUT_PATH, DataEngineeringAgent
from agents.kpi_semantic_agent.agent import KPISemanticAgent
from shared.schemas.data_contracts import (
    AnalysisResult,
    AuditReport,
    CleanedDataset,
    DashboardSpec,
    KPICatalog,
    RawDatasetRef,
)


class BIFlowOrchestrator:
    """Coordinates the BIFlow pipeline across all agents.

    TODO (owner): implement error handling (retry/skip/halt) between stages
    and full execution logging (see execution_log.py) for the Auditor/XAI
    agent to consume, beyond the traceability_log it currently synthesizes
    from each stage's own output.
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

    def run_pipeline(self, raw_dataset: RawDatasetRef) -> AuditReport:
        """Runs the full pipeline end-to-end and returns the final audit report."""
        cleaned = self._run_data_engineering(raw_dataset)
        kpis = self._run_kpi_semantic(cleaned, raw_dataset)
        analysis = self._run_bi_analyst(kpis)
        dashboard = self._run_dashboard(analysis, kpis)
        return self._run_auditor(cleaned, kpis, analysis, dashboard)

    def _run_data_engineering(self, raw_dataset: RawDatasetRef) -> CleanedDataset:
        return DataEngineeringAgent(
            output_path=self.analytical_path, database_url=self.database_url
        ).run(raw_dataset)

    def _run_kpi_semantic(self, cleaned: CleanedDataset, raw_dataset: RawDatasetRef) -> KPICatalog:
        return KPISemanticAgent(business_domain=raw_dataset.business_domain).run(cleaned)

    def _run_bi_analyst(self, kpis: KPICatalog) -> AnalysisResult:
        return BIAnalystAgent().run(kpis)

    def _run_dashboard(self, analysis: AnalysisResult, kpis: KPICatalog) -> DashboardSpec:
        return DashboardAgent(layout_path=self.dashboard_layout_path).run(analysis, kpis)

    def _run_auditor(
        self,
        cleaned: CleanedDataset,
        kpis: KPICatalog,
        analysis: AnalysisResult,
        dashboard: DashboardSpec,
    ) -> AuditReport:
        return AuditorXAIAgent().run(cleaned, kpis, analysis, dashboard)

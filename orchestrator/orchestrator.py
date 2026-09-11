"""BIFlow Orchestrator.

Coordinates the pipeline across all agents. Agents never call each other
directly — every hand-off passes through this class, which is also
responsible for logging each step for the Auditor/XAI agent.
"""

from shared.schemas.data_contracts import (
    AnalysisResult,
    AuditReport,
    CleanedDataset,
    DashboardSpec,
    KPICatalog,
    RawDatasetRef,
)


class BIFlowOrchestrator:
    """
    Coordinates the BIFlow pipeline across all agents.

    TODO (owner): implement dynamic routing, error handling (retry/skip/halt),
    and full execution logging for the Auditor/XAI agent.
    """

    def run_pipeline(self, raw_dataset: RawDatasetRef) -> AuditReport:
        """Runs the full pipeline end-to-end and returns the final audit report."""
        cleaned = self._run_data_engineering(raw_dataset)
        kpis = self._run_kpi_semantic(cleaned)
        analysis = self._run_bi_analyst(kpis)
        dashboard = self._run_dashboard(analysis, kpis)
        return self._run_auditor(cleaned, kpis, analysis, dashboard)

    def _run_data_engineering(self, raw_dataset: RawDatasetRef) -> CleanedDataset:
        """TODO (owner): call the Data Engineering Agent (profiling + cleaning + ETL)."""
        raise NotImplementedError("TODO: call Data Engineering Agent")

    def _run_kpi_semantic(self, cleaned: CleanedDataset) -> KPICatalog:
        """TODO (owner): call the KPI/Semantic Agent to compute the KPI catalog."""
        raise NotImplementedError("TODO: call KPI/Semantic Agent")

    def _run_bi_analyst(self, kpis: KPICatalog) -> AnalysisResult:
        """TODO (owner): call the BI Analyst Agent to detect trends/anomalies/insights."""
        raise NotImplementedError("TODO: call BI Analyst Agent")

    def _run_dashboard(self, analysis: AnalysisResult, kpis: KPICatalog) -> DashboardSpec:
        """TODO (owner): call the Dashboard Generator Agent to build the dashboard."""
        raise NotImplementedError("TODO: call Dashboard Generator Agent")

    def _run_auditor(
        self,
        cleaned: CleanedDataset,
        kpis: KPICatalog,
        analysis: AnalysisResult,
        dashboard: DashboardSpec,
    ) -> AuditReport:
        """TODO (owner): call the Auditor/XAI Agent to validate and explain the run."""
        raise NotImplementedError("TODO: call Auditor/XAI Agent")

"""Shared Pydantic data contracts exchanged between BIFlow agents.

These models are the ONLY objects that should cross agent boundaries. All
agents communicate through the Orchestrator, which passes validated instances
of these models between pipeline stages.

Fields marked `# TODO: confirm with <agent owner>` are provisional — the
owning agent may adjust them, but changes to a shared contract should go
through a PR so downstream consumers aren't broken silently.
"""

from typing import Any

from pydantic import BaseModel


class RawDatasetRef(BaseModel):
    """Input handed to the Data Engineering Agent."""

    dataset_path: str
    dataset_name: str
    business_domain: str  # e.g. "e-commerce", "banking"


class ProfilingReport(BaseModel):
    """Output of the profiling step, input to cleaning."""

    n_rows: int
    n_columns: int
    column_types: dict[str, str]
    missing_values: dict[str, float]
    duplicate_rows: int
    anomalies: list[str]


class CleanedDataset(BaseModel):
    """Output of the Data Engineering Agent, input to KPI agent."""

    dataset_path: str
    data_quality_report: ProfilingReport
    transformations_applied: list[str]


class KPIDefinition(BaseModel):
    """One KPI as defined by the KPI/Semantic Agent."""

    name: str
    formula: str
    description: str
    dimensions: list[str]


class KPICatalog(BaseModel):
    """Output of the KPI/Semantic Agent, input to BI Analyst."""

    kpis: list[KPIDefinition]
    computed_values: dict[str, Any]


class Insight(BaseModel):
    """One insight/recommendation from the BI Analyst Agent."""

    title: str
    description: str
    related_kpi: str
    severity: str  # e.g. "info", "warning", "critical"


class AnalysisResult(BaseModel):
    """Output of the BI Analyst Agent, input to Dashboard Agent."""

    insights: list[Insight]
    trends: dict[str, Any]


class DashboardSpec(BaseModel):
    """Output of the Dashboard Generator Agent, input to Auditor/XAI."""

    dashboard_url: str
    visualizations: list[str]
    kpis_shown: list[str]


class AuditReport(BaseModel):
    """Final output of the Auditor/XAI Agent."""

    validation_status: str
    explanations: dict[str, str]
    traceability_log: list[str]

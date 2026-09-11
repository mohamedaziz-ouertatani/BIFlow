"""Tests for the BI Auditor / XAI Agent, run against the real Olist pipeline output."""

from agents.auditor_xai_agent.agent import AuditorXAIAgent
from agents.bi_analyst_agent.agent import BIAnalystAgent
from agents.dashboard_agent.agent import DashboardAgent
from agents.data_engineering_agent.agent import DataEngineeringAgent
from agents.kpi_semantic_agent.agent import KPISemanticAgent
from shared.schemas.data_contracts import AuditReport, RawDatasetRef

SAMPLE_DIR = "data/sample/olist"


def test_agent_run_produces_audit_report_from_real_pipeline_output(tmp_path):
    raw = RawDatasetRef(
        dataset_path=SAMPLE_DIR, dataset_name="olist_ecommerce", business_domain="e-commerce"
    )
    cleaned = DataEngineeringAgent(output_path=str(tmp_path / "analytical.csv")).run(raw)
    kpis = KPISemanticAgent().run(cleaned)
    analysis = BIAnalystAgent().run(cleaned, kpis)
    dashboard = DashboardAgent(layout_path=str(tmp_path / "layout.json")).run(analysis, kpis)

    result = AuditorXAIAgent().run(cleaned, kpis, analysis, dashboard)

    assert isinstance(result, AuditReport)
    assert result.validation_status in {"passed", "passed_with_warnings", "failed"}
    assert "total_revenue" in result.explanations
    assert len(result.traceability_log) == 4

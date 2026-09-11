"""Tests for BIFlowOrchestrator, run against the real Olist sample end-to-end."""

from orchestrator.orchestrator import BIFlowOrchestrator
from shared.schemas.data_contracts import AuditReport, RawDatasetRef


def test_run_pipeline_produces_audit_report_from_real_sample_data(tmp_path):
    orchestrator = BIFlowOrchestrator(
        analytical_path=str(tmp_path / "analytical.csv"),
        dashboard_layout_path=str(tmp_path / "layout.json"),
    )
    raw = RawDatasetRef(
        dataset_path="data/sample/olist",
        dataset_name="olist_ecommerce",
        business_domain="e-commerce",
    )

    result = orchestrator.run_pipeline(raw)

    assert isinstance(result, AuditReport)
    assert result.validation_status in {"passed", "passed_with_warnings", "failed"}
    assert len(result.traceability_log) == 4
    assert len(result.explanations) > 0

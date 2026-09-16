"""End-to-end integration test running the full BIFlow pipeline on sample data."""

from orchestrator.orchestrator import BIFlowOrchestrator
from shared.schemas.data_contracts import AuditReport, RawDatasetRef


def test_full_pipeline_runs_end_to_end_on_sample_data(tmp_path):
    orchestrator = BIFlowOrchestrator(
        analytical_path=str(tmp_path / "analytical.csv"),
        dashboard_layout_path=str(tmp_path / "dashboard_layout.json"),
    )
    raw = RawDatasetRef(
        dataset_path="data/sample/olist",
        dataset_name="olist_ecommerce",
        business_domain="e-commerce",
    )

    result = orchestrator.run_pipeline(raw)

    assert isinstance(result, AuditReport)
    # The sample data has known data-quality anomalies (missing review
    # comments, duplicate geolocation rows), so "passed" isn't realistic here.
    assert result.validation_status == "passed_with_warnings"
    assert len(result.traceability_log) == 4
    assert "total_revenue" in result.explanations


def test_full_pipeline_runs_end_to_end_on_banking_sample_data(tmp_path):
    orchestrator = BIFlowOrchestrator(
        analytical_path=str(tmp_path / "banking_analytical.csv"),
        dashboard_layout_path=str(tmp_path / "banking_dashboard_layout.json"),
    )
    raw = RawDatasetRef(
        dataset_path="data/sample/banking",
        dataset_name="berka_banking",
        business_domain="banking",
    )

    result = orchestrator.run_pipeline(raw)

    assert isinstance(result, AuditReport)
    assert result.validation_status in ("passed", "passed_with_warnings")
    assert len(result.traceability_log) == 4
    assert "total_transaction_volume" in result.explanations

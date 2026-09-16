"""Tests for BIFlowOrchestrator, run against the real Olist sample end-to-end."""

import pytest
import sqlalchemy

from orchestrator.orchestrator import BIFlowOrchestrator, PipelineStageError
from shared.schemas.data_contracts import AuditReport, RawDatasetRef

TEST_DATABASE_URL = "postgresql://biflow:biflow@localhost:5433/biflow"


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


def test_run_pipeline_loads_into_postgres_when_database_url_given(tmp_path):
    orchestrator = BIFlowOrchestrator(
        analytical_path=str(tmp_path / "analytical.csv"),
        dashboard_layout_path=str(tmp_path / "layout.json"),
        database_url=TEST_DATABASE_URL,
    )
    raw = RawDatasetRef(
        dataset_path="data/sample/olist",
        dataset_name="olist_ecommerce",
        business_domain="e-commerce",
    )

    orchestrator.run_pipeline(raw)

    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        count = conn.execute(sqlalchemy.text("SELECT COUNT(*) FROM orders_analytical")).scalar()
    assert count > 0


def test_run_pipeline_halts_and_wraps_stage_failure(tmp_path, monkeypatch):
    orchestrator = BIFlowOrchestrator(
        analytical_path=str(tmp_path / "analytical.csv"),
        dashboard_layout_path=str(tmp_path / "layout.json"),
    )
    raw = RawDatasetRef(
        dataset_path="data/sample/olist",
        dataset_name="olist_ecommerce",
        business_domain="e-commerce",
    )

    original_error = ValueError("boom")

    def _boom(self, cleaned, kpis):
        raise original_error

    monkeypatch.setattr(BIFlowOrchestrator, "_run_bi_analyst", _boom)

    with pytest.raises(PipelineStageError) as excinfo:
        orchestrator.run_pipeline(raw)

    assert excinfo.value.stage == "bi_analyst"
    assert excinfo.value.__cause__ is original_error

    statuses = [(e.stage, e.status) for e in orchestrator.execution_log.trace.events]
    assert statuses == [
        ("data_engineering", "started"),
        ("data_engineering", "succeeded"),
        ("kpi_semantic", "started"),
        ("kpi_semantic", "succeeded"),
        ("bi_analyst", "started"),
        ("bi_analyst", "failed"),
    ]


def test_run_pipeline_records_execution_log_on_success(tmp_path):
    orchestrator = BIFlowOrchestrator(
        analytical_path=str(tmp_path / "analytical.csv"),
        dashboard_layout_path=str(tmp_path / "layout.json"),
    )
    raw = RawDatasetRef(
        dataset_path="data/sample/olist",
        dataset_name="olist_ecommerce",
        business_domain="e-commerce",
    )

    orchestrator.run_pipeline(raw)

    stages = {e.stage for e in orchestrator.execution_log.trace.events}
    assert stages == {"data_engineering", "kpi_semantic", "bi_analyst", "dashboard", "auditor"}
    started = [e for e in orchestrator.execution_log.trace.events if e.status == "started"]
    succeeded = [e for e in orchestrator.execution_log.trace.events if e.status == "succeeded"]
    assert len(started) == 5
    assert len(succeeded) == 5

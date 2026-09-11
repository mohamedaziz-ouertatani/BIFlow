"""Tests for validators.py: validation status across pipeline outputs."""

from agents.auditor_xai_agent.validators import validate_pipeline_outputs
from shared.schemas.data_contracts import AnalysisResult, CleanedDataset, KPICatalog, ProfilingReport


def _cleaned(n_rows=10, anomalies=None):
    return CleanedDataset(
        dataset_path="x.csv",
        data_quality_report=ProfilingReport(
            n_rows=n_rows,
            n_columns=1,
            column_types={},
            missing_values={},
            duplicate_rows=0,
            anomalies=anomalies or [],
        ),
        transformations_applied=[],
    )


def test_validate_pipeline_outputs_fails_when_no_rows_were_profiled():
    status = validate_pipeline_outputs(
        _cleaned(n_rows=0), KPICatalog(kpis=[], computed_values={}), AnalysisResult(insights=[], trends={})
    )
    assert status == "failed"


def test_validate_pipeline_outputs_warns_when_data_quality_anomalies_present():
    status = validate_pipeline_outputs(
        _cleaned(anomalies=["orders: 3 duplicate rows"]),
        KPICatalog(kpis=[], computed_values={}),
        AnalysisResult(insights=[], trends={}),
    )
    assert status == "passed_with_warnings"


def test_validate_pipeline_outputs_warns_when_insight_severity_is_warning_or_critical():
    from shared.schemas.data_contracts import Insight

    status = validate_pipeline_outputs(
        _cleaned(),
        KPICatalog(kpis=[], computed_values={}),
        AnalysisResult(
            insights=[
                Insight(
                    title="x", description="y", related_kpi="z", severity="warning"
                )
            ],
            trends={},
        ),
    )
    assert status == "passed_with_warnings"


def test_validate_pipeline_outputs_passes_when_clean_and_no_concerning_insights():
    status = validate_pipeline_outputs(
        _cleaned(), KPICatalog(kpis=[], computed_values={}), AnalysisResult(insights=[], trends={})
    )
    assert status == "passed"

"""Tests for BIFlowOrchestrator.

TODO (owner): once _run_* methods call real agents (or mocks of them), test:
- run_pipeline() calls each stage in order and passes the right types through
- error handling behavior (retry/skip/halt) once implemented
"""

import pytest

from orchestrator.orchestrator import BIFlowOrchestrator
from shared.schemas.data_contracts import RawDatasetRef


def test_run_pipeline_not_implemented():
    """Stub test: run_pipeline should currently raise NotImplementedError."""
    orchestrator = BIFlowOrchestrator()
    raw = RawDatasetRef(
        dataset_path="data/sample/olist",
        dataset_name="olist_ecommerce",
        business_domain="e-commerce",
    )
    with pytest.raises(NotImplementedError):
        orchestrator.run_pipeline(raw)

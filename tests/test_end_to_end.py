"""End-to-end integration test running the full BIFlow pipeline on sample data.

TODO (owner, Person E): once all agents are implemented, point this at
data/sample/ and assert the pipeline produces a valid AuditReport with
validation_status == "passed" (or similar).
"""

import pytest

from orchestrator.orchestrator import BIFlowOrchestrator
from shared.schemas.data_contracts import RawDatasetRef


def test_full_pipeline_not_implemented():
    """Stub test: the full pipeline should currently raise NotImplementedError."""
    orchestrator = BIFlowOrchestrator()
    raw = RawDatasetRef(
        dataset_path="data/sample/olist",
        dataset_name="olist_ecommerce",
        business_domain="e-commerce",
    )
    with pytest.raises(NotImplementedError):
        orchestrator.run_pipeline(raw)

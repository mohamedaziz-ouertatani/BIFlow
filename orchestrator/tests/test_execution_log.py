"""Tests for orchestrator.execution_log.ExecutionLogger."""

from orchestrator.execution_log import ExecutionLogger


def test_log_appends_a_trace_event():
    logger = ExecutionLogger(run_id="run-1")

    logger.log("data_engineering", "started")

    assert len(logger.trace.events) == 1
    event = logger.trace.events[0]
    assert event.stage == "data_engineering"
    assert event.status == "started"
    assert event.details == {}


def test_log_records_details():
    logger = ExecutionLogger(run_id="run-1")

    logger.log("data_engineering", "failed", details={"error": "boom"})

    assert logger.trace.events[0].details == {"error": "boom"}


def test_as_traceability_log_formats_each_event():
    logger = ExecutionLogger(run_id="run-1")
    logger.log("data_engineering", "started")
    logger.log("data_engineering", "succeeded")

    lines = logger.as_traceability_log()

    assert len(lines) == 2
    assert "data_engineering" in lines[0]
    assert "started" in lines[0]
    assert "data_engineering" in lines[1]
    assert "succeeded" in lines[1]

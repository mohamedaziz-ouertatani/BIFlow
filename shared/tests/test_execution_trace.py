"""Tests for shared.schemas.execution_trace.ExecutionTrace."""

from datetime import datetime

from shared.schemas.execution_trace import ExecutionTrace, TraceEvent


def test_add_event_appends_to_events():
    trace = ExecutionTrace(run_id="run-1", events=[])
    event = TraceEvent(timestamp=datetime.now(), stage="data_engineering", status="started")

    trace.add_event(event)

    assert trace.events == [event]


def test_add_event_preserves_order_across_multiple_calls():
    trace = ExecutionTrace(run_id="run-1", events=[])
    first = TraceEvent(timestamp=datetime.now(), stage="data_engineering", status="started")
    second = TraceEvent(timestamp=datetime.now(), stage="data_engineering", status="succeeded")

    trace.add_event(first)
    trace.add_event(second)

    assert trace.events == [first, second]

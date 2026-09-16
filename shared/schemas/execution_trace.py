"""Shared execution trace / log schema.

Used by the Orchestrator to record every pipeline step, and consumed by the
Auditor/XAI Agent to build traceability and explanations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TraceEvent(BaseModel):
    """A single logged event in the pipeline's execution."""

    timestamp: datetime
    stage: str  # e.g. "data_engineering", "kpi_semantic", "bi_analyst"
    status: str  # e.g. "started", "succeeded", "failed", "skipped"
    details: dict[str, Any] = {}
    # TODO: confirm with orchestrator owner — should this include a duration_ms field?


class ExecutionTrace(BaseModel):
    """The full ordered trace of a pipeline run."""

    run_id: str
    events: list[TraceEvent]

    # Appends an event to the trace (in-memory for the run's duration).
    def add_event(self, event: TraceEvent) -> None:
        """Append an event to the trace (in-memory for the run's duration)."""
        self.events.append(event)

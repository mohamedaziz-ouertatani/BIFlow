"""Execution logging helpers for the Orchestrator.

Wraps shared.schemas.execution_trace.ExecutionTrace with the in-memory
recording and formatting logic the Orchestrator needs for step-by-step
tracing of one pipeline run. Kept in-memory (MVP scope) rather than
persisted to a file or DB — the trace lives only for the run's duration.
"""

from datetime import datetime

from shared.schemas.execution_trace import ExecutionTrace, TraceEvent


class ExecutionLogger:
    """Records pipeline execution events into an in-memory ExecutionTrace."""

    def __init__(self, run_id: str) -> None:
        self.trace = ExecutionTrace(run_id=run_id, events=[])

    def log(self, stage: str, status: str, details: dict | None = None) -> None:
        """Record one pipeline stage transition."""
        self.trace.add_event(
            TraceEvent(
                timestamp=datetime.now(),
                stage=stage,
                status=status,
                details=details or {},
            )
        )

    def as_traceability_log(self) -> list[str]:
        """Render the trace as a flat list of human-readable strings."""
        lines = []
        for event in self.trace.events:
            line = f"{event.timestamp.isoformat()} {event.stage}: {event.status}"
            if event.details:
                line += f" ({event.details})"
            lines.append(line)
        return lines

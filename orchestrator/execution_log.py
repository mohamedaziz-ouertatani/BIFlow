"""Execution logging helpers for the Orchestrator.

Wraps shared.schemas.execution_trace.ExecutionTrace with the persistence and
formatting logic the Orchestrator needs (e.g. writing to a file/DB, and
producing the traceability_log consumed by the Auditor/XAI agent).
"""

from shared.schemas.execution_trace import ExecutionTrace, TraceEvent


class ExecutionLogger:
    """Records pipeline execution events into an ExecutionTrace.

    TODO (owner): decide on a persistence backend (file, DB table, or
    in-memory for MVP) and implement accordingly.
    """

    def __init__(self, run_id: str) -> None:
        self.trace = ExecutionTrace(run_id=run_id, events=[])

    def log(self, stage: str, status: str, details: dict | None = None) -> None:
        """Record one pipeline stage transition.

        TODO (owner): implement — append a TraceEvent and persist it.
        """
        raise NotImplementedError("TODO: implement stage logging")

    def as_traceability_log(self) -> list[str]:
        """Render the trace as a flat list of human-readable strings.

        TODO (owner): implement formatting for AuditReport.traceability_log.
        """
        raise NotImplementedError("TODO: implement traceability log formatting")

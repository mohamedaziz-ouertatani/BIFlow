"""FastAPI backend serving the dashboard layout JSON to the Next.js frontend.

Replaces the old Streamlit app.py: the frontend polls GET /api/dashboard
instead of a Python process re-rendering server-side on every load.
"""

import json
import os
import queue
import threading

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.dashboard_agent.agent import DEFAULT_LAYOUT_PATH
from agents.dashboard_agent.nl_query import (
    OllamaTimeoutError,
    OllamaUnavailableError,
    generate_answer,
)
from agents.dashboard_agent.report import build_pdf
from orchestrator.orchestrator import BIFlowOrchestrator, PipelineStageError
from shared.schemas.data_contracts import RawDatasetRef

DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000"]

# The only business domains the pipeline knows how to run — domain is
# interpolated into a filesystem path, so it must be checked against this
# allowlist rather than passed through as free text.
ALLOWED_DOMAINS = {"e-commerce", "banking", "telco"}

# Where each domain's raw sample dataset lives, for live-triggered runs.
DOMAIN_DATASETS: dict[str, tuple[str, str]] = {
    "e-commerce": ("data/sample/olist", "olist"),
    "banking": ("data/sample/banking", "banking"),
    "telco": ("data/sample/telco", "telco"),
}

_STATUS_TO_EVENT_TYPE = {
    "started": "stage_started",
    "succeeded": "stage_succeeded",
    "failed": "stage_failed",
}


# Builds the FastAPI app with CORS and the health/dashboard routes.
def create_app(
    layout_path: str | None = None, allowed_origins: list[str] | None = None
) -> FastAPI:
    """Builds the FastAPI app. layout_path/allowed_origins default from env/constants
    so tests can override them without touching global state."""
    resolved_layout_path = layout_path or os.environ.get(
        "DASHBOARD_LAYOUT_PATH", DEFAULT_LAYOUT_PATH
    )
    origins = allowed_origins or os.environ.get(
        "ALLOWED_ORIGINS", ",".join(DEFAULT_ALLOWED_ORIGINS)
    ).split(",")

    app = FastAPI(title="BIFlow Dashboard API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Resolves which layout file to read: a domain-specific one (written ahead
    # of time per business domain, e.g. dashboard_layout_banking.json) when a
    # domain is requested, otherwise the path the live pipeline run writes to.
    def _layout_path_for(domain: str | None) -> str:
        if not domain:
            return resolved_layout_path
        if domain not in ALLOWED_DOMAINS:
            raise HTTPException(status_code=404, detail=f"Unknown domain: {domain!r}")
        directory = os.path.dirname(resolved_layout_path) or "."
        return os.path.join(directory, f"dashboard_layout_{domain}.json")

    # Simple liveness check for the API.
    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Runs the real pipeline for a domain and streams each stage's start/success/failure
    # as Server-Sent Events, so the landing page's animation reflects the actual run
    # instead of a fixed timeline. Writes its result to that domain's layout file.
    @app.get("/api/pipeline/run")
    def run_pipeline(domain: str) -> StreamingResponse:
        layout_path = _layout_path_for(domain)  # validates domain against ALLOWED_DOMAINS
        dataset_path, dataset_name = DOMAIN_DATASETS[domain]
        events: queue.Queue[dict | None] = queue.Queue()

        def on_event(stage: str, status: str, details: dict) -> None:
            payload: dict = {"type": _STATUS_TO_EVENT_TYPE[status], "stage": stage}
            if details.get("error"):
                payload["error"] = details["error"]
            events.put(payload)

        def run() -> None:
            pipeline = BIFlowOrchestrator(dashboard_layout_path=layout_path, on_event=on_event)
            raw_dataset = RawDatasetRef(
                dataset_path=dataset_path, dataset_name=dataset_name, business_domain=domain
            )
            try:
                pipeline.run_pipeline(raw_dataset)
                events.put({"type": "pipeline_succeeded"})
            except PipelineStageError as exc:
                events.put({"type": "pipeline_failed", "stage": exc.stage, "error": str(exc)})
            finally:
                events.put(None)

        threading.Thread(target=run, daemon=True).start()

        def event_stream():
            while True:
                event = events.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # Serves the latest dashboard layout JSON written by DashboardAgent, optionally scoped to a domain.
    @app.get("/api/dashboard")
    def dashboard(domain: str | None = None) -> dict:
        path = _layout_path_for(domain)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="No dashboard data yet — run the pipeline first.")
        with open(path) as f:
            return json.load(f)

    # Serves a downloadable PDF snapshot of the current dashboard layout, optionally scoped to a domain.
    @app.get("/api/report.pdf")
    def report(domain: str | None = None) -> Response:
        path = _layout_path_for(domain)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="No dashboard data yet — run the pipeline first.")
        with open(path) as f:
            layout = json.load(f)
        pdf_bytes = build_pdf(layout)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=biflow_report.pdf"},
        )

    class QueryRequest(BaseModel):
        question: str

    class QueryResponse(BaseModel):
        answer: str

    # Answers a natural-language question grounded in the current dashboard layout via a local LLM.
    @app.post("/api/query", response_model=QueryResponse)
    def query(request: QueryRequest, domain: str | None = None) -> QueryResponse:
        path = _layout_path_for(domain)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="No dashboard data yet — run the pipeline first.")
        with open(path) as f:
            layout = json.load(f)
        try:
            answer = generate_answer(request.question, layout)
        except OllamaTimeoutError:
            raise HTTPException(status_code=504, detail="Local LLM timed out.")
        except OllamaUnavailableError:
            raise HTTPException(status_code=503, detail="Local LLM unavailable — is Ollama running?")
        return QueryResponse(answer=answer)

    return app

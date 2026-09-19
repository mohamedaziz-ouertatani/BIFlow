"""FastAPI backend serving the dashboard layout JSON to the Next.js frontend.

Replaces the old Streamlit app.py: the frontend polls GET /api/dashboard
instead of a Python process re-rendering server-side on every load.
"""

import json
import os
import queue
import threading

import pandas as pd
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from agents.dashboard_agent.agent import DEFAULT_LAYOUT_PATH
from agents.data_engineering_agent.agent import DEFAULT_OUTPUT_PATH
from agents.dashboard_agent.nl_query import (
    OllamaTimeoutError,
    OllamaUnavailableError,
    generate_answer,
)
from agents.dashboard_agent.report import build_pdf
from agents.kpi_semantic_agent.row_filters import filter_rows
from orchestrator.orchestrator import BIFlowOrchestrator, PipelineStageError
from shared.schemas.data_contracts import RawDatasetRef

DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000"]

# The only business domains the pipeline knows how to run — domain is
# interpolated into a filesystem path, so it must be checked against this
# allowlist rather than passed through as free text.
ALLOWED_DOMAINS = {"e-commerce", "banking", "telco"}

# Where each domain's dataset lives, for live-triggered runs. BIFLOW_DATASET_SET
# picks the set: "raw" (the full, gitignored datasets, the default) or "sample"
# (the small committed samples, used by the Playwright end-to-end tests).
# Directory names differ between the sets (berka vs banking), so these are two
# full mappings rather than one root.
DATASET_SETS: dict[str, dict[str, tuple[str, str]]] = {
    "raw": {
        "e-commerce": ("data/raw/olist", "olist"),
        "banking": ("data/raw/berka", "banking"),
        "telco": ("data/raw/telco", "telco"),
    },
    "sample": {
        "e-commerce": ("data/sample/olist", "olist"),
        "banking": ("data/sample/banking", "banking"),
        "telco": ("data/sample/telco", "telco"),
    },
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
    resolved_analytical_path = os.environ.get("ANALYTICAL_TABLE_PATH", DEFAULT_OUTPUT_PATH)
    dataset_set = os.environ.get("BIFLOW_DATASET_SET", "raw")
    if dataset_set not in DATASET_SETS:
        raise ValueError(
            f"BIFLOW_DATASET_SET must be one of {sorted(DATASET_SETS)}, got {dataset_set!r}"
        )
    domain_datasets = DATASET_SETS[dataset_set]
    origins = allowed_origins or os.environ.get(
        "ALLOWED_ORIGINS", ",".join(DEFAULT_ALLOWED_ORIGINS)
    ).split(",")

    app = FastAPI(title="BIFlow Dashboard API")
    # CORS: the browser loads the dashboard from :3000 but calls this API on :8000 (a different
    # origin), and refuses the response unless the API explicitly allows that origin.
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

    # Resolves which analytical table CSV to read: a domain-specific one
    # (written by a live-triggered run for that domain, e.g.
    # analytical_table_banking.csv) when a domain is given, otherwise the
    # path a domain-less CLI run writes to. Mirrors _layout_path_for.
    def _analytical_path_for(domain: str | None) -> str:
        if not domain:
            return resolved_analytical_path
        if domain not in ALLOWED_DOMAINS:
            raise HTTPException(status_code=404, detail=f"Unknown domain: {domain!r}")
        directory = os.path.dirname(resolved_analytical_path) or "."
        base, ext = os.path.splitext(os.path.basename(resolved_analytical_path))
        return os.path.join(directory, f"{base}_{domain}{ext}")

    _analytical_df_cache: dict[str, tuple[float, pd.DataFrame]] = {}

    # Loads an analytical CSV into memory, cached by (path, mtime) so repeat
    # drill-down requests don't re-read a potentially million-row file.
    def _load_analytical_df(path: str) -> pd.DataFrame:
        # The file's modification time changes whenever a pipeline run rewrites the CSV,
        # which invalidates the cached copy.
        mtime = os.path.getmtime(path)
        cached = _analytical_df_cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
        df = pd.read_csv(path, low_memory=False)
        _analytical_df_cache[path] = (mtime, df)
        return df

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
        analytical_path = _analytical_path_for(domain)
        dataset_path, dataset_name = domain_datasets[domain]
        # How streaming works: the orchestrator is blocking code, so it runs in a background thread and
        # pushes each stage event into this thread-safe queue. The generator below drains the queue and
        # sends each item to the browser as a Server-Sent Event; `None` is the 'stream is over' marker.
        events: queue.Queue[dict | None] = queue.Queue()

        # Called by the orchestrator (in the worker thread) on every stage transition; translates it
        # into the event shape the frontend's usePipelineRun hook expects.
        def on_event(stage: str, status: str, details: dict) -> None:
            payload: dict = {"type": _STATUS_TO_EVENT_TYPE[status], "stage": stage}
            if details.get("error"):
                payload["error"] = details["error"]
            events.put(payload)

        def run() -> None:
            pipeline = BIFlowOrchestrator(
                analytical_path=analytical_path,
                dashboard_layout_path=layout_path,
                on_event=on_event,
            )
            raw_dataset = RawDatasetRef(
                dataset_path=dataset_path, dataset_name=dataset_name, business_domain=domain
            )
            try:
                pipeline.run_pipeline(raw_dataset)
                events.put({"type": "pipeline_succeeded"})
            except PipelineStageError as exc:
                events.put({"type": "pipeline_failed", "stage": exc.stage, "error": str(exc)})
            finally:
                # Always send the end marker (even after an unexpected error) so the stream stops
                # and the HTTP response ends instead of hanging forever.
                events.put(None)

        # daemon=True: don't keep the server process alive just for this worker thread.
        threading.Thread(target=run, daemon=True).start()

        def event_stream():
            while True:
                event = events.get()
                if event is None:
                    break
                # SSE wire format: a message is 'data: <payload>' followed by a blank line; the browser's
                # EventSource splits the stream on that blank line.
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

    DRILLDOWN_ROW_LIMIT = 50

    # Serves the raw analytical-table rows behind one KPI's value, optionally scoped to a month.
    @app.get("/api/drilldown")
    def drilldown(domain: str, kpi: str, month: str | None = None) -> dict:
        path = _analytical_path_for(domain)  # validates domain against ALLOWED_DOMAINS
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="No dashboard data yet — run the pipeline first.")
        df = _load_analytical_df(path)
        try:
            matching = filter_rows(df, domain, kpi, month)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown KPI: {kpi!r}")
        # Only the first rows are sent (the table can hold ~100k); total_rows tells the UI how many matched.
        page = matching.head(DRILLDOWN_ROW_LIMIT)
        return {
            "total_rows": int(len(matching)),
            "columns": list(page.columns),
            # Round-trips through pandas' JSON writer so NaN becomes null and timestamps become plain values;
            # page.to_dict() would leave NaN in, which isn't valid JSON.
            "rows": json.loads(page.to_json(orient="records")),
        }

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
        question: str = Field(min_length=1, max_length=1000)

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

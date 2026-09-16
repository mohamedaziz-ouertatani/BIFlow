"""FastAPI backend serving the dashboard layout JSON to the Next.js frontend.

Replaces the old Streamlit app.py: the frontend polls GET /api/dashboard
instead of a Python process re-rendering server-side on every load.
"""

import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.dashboard_agent.agent import DEFAULT_LAYOUT_PATH
from agents.dashboard_agent.nl_query import (
    OllamaTimeoutError,
    OllamaUnavailableError,
    generate_answer,
)

DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000"]


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

    # Simple liveness check for the API.
    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Serves the latest dashboard layout JSON written by DashboardAgent.
    @app.get("/api/dashboard")
    def dashboard() -> dict:
        if not os.path.exists(resolved_layout_path):
            raise HTTPException(status_code=404, detail="No dashboard data yet — run the pipeline first.")
        with open(resolved_layout_path) as f:
            return json.load(f)

    class QueryRequest(BaseModel):
        question: str

    class QueryResponse(BaseModel):
        answer: str

    # Answers a natural-language question grounded in the current dashboard layout via a local LLM.
    @app.post("/api/query", response_model=QueryResponse)
    def query(request: QueryRequest) -> QueryResponse:
        if not os.path.exists(resolved_layout_path):
            raise HTTPException(status_code=404, detail="No dashboard data yet — run the pipeline first.")
        with open(resolved_layout_path) as f:
            layout = json.load(f)
        try:
            answer = generate_answer(request.question, layout)
        except OllamaTimeoutError:
            raise HTTPException(status_code=504, detail="Local LLM timed out.")
        except OllamaUnavailableError:
            raise HTTPException(status_code=503, detail="Local LLM unavailable — is Ollama running?")
        return QueryResponse(answer=answer)

    return app

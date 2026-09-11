"""FastAPI backend serving the dashboard layout JSON to the Next.js frontend.

Replaces the old Streamlit app.py: the frontend polls GET /api/dashboard
instead of a Python process re-rendering server-side on every load.
"""

import json
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agents.dashboard_agent.agent import DEFAULT_LAYOUT_PATH

DEFAULT_ALLOWED_ORIGINS = ["http://localhost:3000"]


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
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/dashboard")
    def dashboard() -> dict:
        if not os.path.exists(resolved_layout_path):
            raise HTTPException(status_code=404, detail="No dashboard data yet — run the pipeline first.")
        with open(resolved_layout_path) as f:
            return json.load(f)

    return app

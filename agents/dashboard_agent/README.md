# Dashboard Generator Agent

**Owner:** Person D

## Purpose
Builds the data behind the interactive dashboard and serves it to the
Next.js frontend (`frontend/`). Consumes the outputs of the KPI/Semantic
and BI Analyst agents and produces a runnable dashboard plus a spec for
the Auditor/XAI agent.

## Input
`shared.schemas.data_contracts.AnalysisResult`, `shared.schemas.data_contracts.KPICatalog`

## Output
`shared.schemas.data_contracts.DashboardSpec`

## How it works
1. **`layout_builder.build_layout(analysis, kpis)`** — builds a JSON-serializable
   layout: one `kpi_cards` entry per KPI (name, label, value) and one
   `insights` entry per `Insight` (title, description, severity).
2. **`DashboardAgent.run(analysis, kpis)`** — builds the layout, writes it to
   `data/processed/dashboard_layout.json` (configurable via
   `layout_path`), and returns a `DashboardSpec`.
3. **`api.py`** — a small FastAPI app (`GET /api/dashboard`, `GET /api/health`)
   that reads that layout JSON (path via the `DASHBOARD_LAYOUT_PATH` env
   var, falling back to the default) and serves it as JSON, with CORS open
   for the frontend's origin. The **`frontend/`** Next.js app polls this
   every 5s and renders it (see `frontend/README.md`). Run the API with
   `uvicorn agents.dashboard_agent.api:create_app --factory`, or via
   `docker-compose up dashboard_agent` (served on port 8000).

This used to be a Streamlit app (`app.py`, since removed) that rendered
the layout itself, server-side, on every page load. It's now a pure JSON
API — the frontend owns rendering and polling.

## Key files
- `agent.py` — main agent entrypoint (`DashboardAgent`), called by the Orchestrator
- `layout_builder.py` — builds the JSON-serializable dashboard layout
- `api.py` — FastAPI backend serving the layout to the frontend, tested with `TestClient`

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
uvicorn agents.dashboard_agent.api:create_app --factory --reload
```

## TODO
- [x] Implement core logic
- [x] Write unit tests against sample data in `data/sample/`
- [x] Swap in real `AnalysisResult` insights (BI Analyst Agent now exists)
- [x] Replace the Streamlit UI with a Next.js frontend + FastAPI backend
- [ ] Add a chart (e.g. revenue or review-score trend) — `BIAnalystAgent`
  already computes real monthly trends (`AnalysisResult.trends["monthly"]`),
  but the layout/frontend only show current KPI values and text insights

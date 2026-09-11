# Dashboard Generator Agent

**Owner:** Person D

## Purpose
Builds the interactive dashboard that presents KPIs and insights to
end users. Consumes the outputs of the KPI/Semantic and BI Analyst agents
and produces a runnable dashboard plus a spec for the Auditor/XAI agent.

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
3. **`app.py`** — a Streamlit page that reads that layout JSON (path via the
   `DASHBOARD_LAYOUT_PATH` env var, falling back to the default) and renders
   a metric per KPI card plus an insights panel (colored by severity:
   info/warning/critical). Run directly with `streamlit run app.py`, or via
   `docker-compose up dashboard_agent` (served on port 8501).

Note: the BI Analyst Agent (which produces `AnalysisResult`) isn't built
yet — `DashboardAgent` was implemented and tested against the real
`AnalysisResult` contract using hand-built `Insight` objects, so it's ready
to consume real insights once that agent exists.

## Key files
- `agent.py` — main agent entrypoint (`DashboardAgent`), called by the Orchestrator
- `layout_builder.py` — builds the JSON-serializable dashboard layout
- `app.py` — Streamlit entrypoint, tested headlessly via `streamlit.testing.v1.AppTest`

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
streamlit run app.py
```

## TODO
- [x] Implement core logic
- [x] Write unit tests against sample data in `data/sample/`
- [ ] Swap in real `AnalysisResult` insights once the BI Analyst Agent exists
- [ ] Add a chart (e.g. revenue or review-score trend) once trend data is available

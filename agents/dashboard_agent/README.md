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

## Key files
- `agent.py` — main agent entrypoint, called by the Orchestrator
- `layout_builder.py` — builds the dashboard layout spec from KPIs + insights
- `app.py` — Streamlit/Dash entrypoint

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
streamlit run app.py
```

## TODO
- [ ] Implement core logic
- [ ] Write unit tests against sample data in `data/sample/`
- [ ] Document any LLM prompts used in `prompts/` (create if needed)

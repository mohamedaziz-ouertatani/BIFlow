# Orchestrator

**Owner:** Person E

## Purpose
Coordinates the BIFlow pipeline end-to-end. Calls each agent in sequence
(Data Engineering → KPI/Semantic → BI Analyst → Dashboard → Auditor/XAI),
passing validated Pydantic objects between them. Agents never call each
other directly — all hand-offs go through the Orchestrator.

## Input
`shared.schemas.data_contracts.RawDatasetRef`

## Output
`shared.schemas.data_contracts.AuditReport`

## How it works
`BIFlowOrchestrator.run_pipeline(raw_dataset)` instantiates and calls each
agent directly, in-process:

1. `DataEngineeringAgent(output_path=self.analytical_path, database_url=self.database_url).run(raw_dataset)` → `CleanedDataset`
2. `KPISemanticAgent(business_domain=raw_dataset.business_domain).run(cleaned)` → `KPICatalog`
3. `BIAnalystAgent().run(kpis)` → `AnalysisResult`
4. `DashboardAgent(layout_path=self.dashboard_layout_path).run(analysis, kpis)` → `DashboardSpec`
5. `AuditorXAIAgent().run(cleaned, kpis, analysis, dashboard)` → `AuditReport`

`analytical_path` / `dashboard_layout_path` / `database_url` are constructor
params (defaulting to each agent's own default, and `None` for
`database_url`) so tests can point at a temp dir and stay Postgres-free
unless a test explicitly opts in.

Note: because the Orchestrator imports every agent class directly, its
Docker image needs every agent's runtime dependencies (pandas, streamlit,
sqlalchemy, psycopg2) installed too — see `requirements.txt`. This works
for the current single-process design; a distributed setup (agents as
separate services called over RPC) would need a different dependency/build
story.

## Key files
- `orchestrator.py` — main orchestrator class, one method per pipeline stage
- `execution_log.py` — execution trace/logging (not yet wired in — see TODO)

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [x] Wire real agent calls into each `_run_*` method
- [x] Write an end-to-end test against sample data in `data/sample/`
- [ ] Implement error handling (retry/skip/halt) between stages
- [ ] Wire `execution_log.py` for step-by-step tracing (currently the
  Auditor/XAI agent synthesizes its `traceability_log` from each stage's
  own output instead)

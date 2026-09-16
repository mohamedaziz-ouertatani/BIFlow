# BI Auditor / XAI Agent

**Owner:** Person E

## Purpose
Validates the outputs of every pipeline stage and produces explanations and
a traceability log, so the final dashboard and insights are trustworthy and
auditable. This is the last stage of the pipeline.

## Input
`shared.schemas.data_contracts.CleanedDataset`, `KPICatalog`, `AnalysisResult`, `DashboardSpec`

## Output
`shared.schemas.data_contracts.AuditReport`

## How it works
1. **`validators.validate_pipeline_outputs(cleaned, kpis, analysis)`** —
   `"failed"` if no rows were profiled; `"passed_with_warnings"` if the
   cleaning report has anomalies or any insight has `warning`/`critical`
   severity; `"passed"` otherwise.
2. **`explainer.generate_explanations(kpis, analysis)`** — one explanation
   per KPI (its description, formula, and computed value) and one per
   insight (its description).
3. **`agent.py`** — wires both together, plus a `traceability_log`
   synthesized from the four inputs it receives (row counts,
   transformation count, KPI/insight counts, dashboard URL) — no separate
   execution trace needs to be threaded through.

## Key files
- `agent.py` — main agent entrypoint (`AuditorXAIAgent`), called by the Orchestrator
- `validators.py` — validation rules across pipeline outputs
- `explainer.py` — explainability (XAI) logic for KPIs and insights

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [x] Implement core logic
- [x] Write unit tests against sample data in `data/sample/`
- [x] Fill in `docs/xai_report_template.md` with a real rendered example

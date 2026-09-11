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

## Key files
- `agent.py` — main agent entrypoint, called by the Orchestrator
- `validators.py` — validation rules across pipeline outputs
- `explainer.py` — explainability (XAI) logic for KPIs and insights

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [ ] Implement core logic
- [ ] Write unit tests against sample data in `data/sample/`
- [ ] Document any LLM prompts used in `prompts/` (create if needed)
- [ ] Fill in `docs/xai_report_template.md`

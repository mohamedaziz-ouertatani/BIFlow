# BI Semantic & KPI Agent

**Owner:** Person B

## Purpose
Defines the KPIs relevant to the business domain and computes their values
against the cleaned dataset produced by the Data Engineering Agent. Its
output is the semantic layer the BI Analyst Agent builds insights on top of.

## Input
`shared.schemas.data_contracts.CleanedDataset`

## Output
`shared.schemas.data_contracts.KPICatalog`

## Key files
- `agent.py` — main agent entrypoint, called by the Orchestrator
- `kpi_definitions.py` — KPI definitions per business domain

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [ ] Implement core logic
- [ ] Write unit tests against sample data in `data/sample/`
- [ ] Document any LLM prompts used in `prompts/` (create if needed)
- [ ] Fill in `docs/kpi_catalog.md` with the finalized KPI list

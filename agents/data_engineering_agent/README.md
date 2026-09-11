# Data Engineering Agent

**Owner:** Person A

## Purpose
Profiles raw datasets, applies data-quality cleaning, and runs ETL to
produce a cleaned, analysis-ready dataset. It is the first agent in the
pipeline and its output feeds the KPI/Semantic Agent.

## Input
`shared.schemas.data_contracts.RawDatasetRef`

## Output
`shared.schemas.data_contracts.CleanedDataset` (which embeds a `ProfilingReport`)

## Key files
- `agent.py` — main agent entrypoint, called by the Orchestrator
- `profiler.py` — dataset profiling (schema, missing values, duplicates, anomalies)
- `cleaner.py` — data-quality cleaning rules
- `etl.py` — final transform/load steps
- `tools/` — any LangChain/LangGraph tools this agent exposes

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [ ] Implement core logic
- [ ] Write unit tests against sample data in `data/sample/`
- [ ] Document any LLM prompts used in `prompts/` (create if needed)

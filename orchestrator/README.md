# Orchestrator

**Owner:** Person E

## Purpose
Coordinates the BIFlow pipeline end-to-end. Calls each agent in sequence
(Data Engineering → KPI/Semantic → BI Analyst → Dashboard → Auditor/XAI),
passing validated Pydantic objects between them and logging every step for
the Auditor/XAI agent to consume. Agents never call each other directly —
all hand-offs go through the Orchestrator.

## Input
`shared.schemas.data_contracts.RawDatasetRef`

## Output
`shared.schemas.data_contracts.AuditReport`

## Key files
- `orchestrator.py` — main orchestrator class, one method per pipeline stage
- `execution_log.py` — execution trace/logging used by the Auditor/XAI agent

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [ ] Implement dynamic routing between agents
- [ ] Implement error handling (retry/skip/halt) between stages
- [ ] Implement full execution logging via `execution_log.py`
- [ ] Write unit tests against sample data in `data/sample/`

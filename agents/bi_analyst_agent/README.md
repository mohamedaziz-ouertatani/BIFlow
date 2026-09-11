# BI Analyst Agent

**Owner:** Person C

## Purpose
Analyzes the KPI catalog to detect trends and anomalies, then generates
business insights and recommendations. Its output drives what the Dashboard
Generator Agent visualizes.

## Input
`shared.schemas.data_contracts.KPICatalog`

## Output
`shared.schemas.data_contracts.AnalysisResult`

## Key files
- `agent.py` — main agent entrypoint, called by the Orchestrator
- `trend_detection.py` — trend/anomaly detection over KPI values
- `insight_generator.py` — turns trends into human-readable insights

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [ ] Implement core logic
- [ ] Write unit tests against sample data in `data/sample/`
- [ ] Document any LLM prompts used in `prompts/` (create if needed)

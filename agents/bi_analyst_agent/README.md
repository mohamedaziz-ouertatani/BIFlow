# BI Analyst Agent

**Owner:** Person C

## Purpose
Analyzes the KPI catalog to flag which KPIs are healthy vs. concerning and
generates human-readable insights from that. Its output drives what the
Dashboard Generator Agent visualizes.

## Input
`shared.schemas.data_contracts.KPICatalog`

## Output
`shared.schemas.data_contracts.AnalysisResult`

## How it works
The agent only receives a single `KPICatalog` snapshot per run — there's no
historical data to compare against, so "trend detection" here means
threshold-based evaluation rather than time-series analysis:

1. **`trend_detection.detect_trends(kpis)`** — evaluates each KPI that has a
   natural business threshold (`on_time_delivery_rate` ≥ 0.9,
   `average_review_score` ≥ 4.0) and flags it `"healthy"` or `"concerning"`.
   Other KPIs (revenue, AOV, order count) have no natural threshold and
   aren't evaluated.
2. **`insight_generator.generate_insights(kpis, trends)`** — turns each
   evaluation into an `Insight`: `info` severity when healthy, `warning`
   when concerning.

## Key files
- `agent.py` — main agent entrypoint (`BIAnalystAgent`), called by the Orchestrator
- `trend_detection.py` — threshold-based KPI evaluation
- `insight_generator.py` — turns evaluations into human-readable insights

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [x] Implement core logic
- [x] Write unit tests against sample data in `data/sample/`
- [ ] Add real time-series trend detection once historical KPI data exists
  (would need `BIAnalystAgent` to also receive the analytical dataset, not
  just the KPICatalog — see `docs/architecture.md` open questions)

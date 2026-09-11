# BI Analyst Agent

**Owner:** Person C

## Purpose
Analyzes the pipeline output to flag which KPIs are healthy vs. concerning
*and* detect real month-over-month trends, generating human-readable
insights from both. Its output drives what the Dashboard Generator Agent
visualizes.

## Input
`shared.schemas.data_contracts.CleanedDataset`, `shared.schemas.data_contracts.KPICatalog`

## Output
`shared.schemas.data_contracts.AnalysisResult`

## How it works
Two kinds of trend detection, combined:

1. **Threshold evaluation** (`trend_detection.detect_trends(kpis)`) — the
   single `KPICatalog` snapshot has no history to compare against, so this
   evaluates each KPI with a natural business threshold
   (`on_time_delivery_rate` ≥ 0.9, `average_review_score` ≥ 4.0) and flags
   it `"healthy"` or `"concerning"`.
2. **Real month-over-month trends** (`monthly_trends.compute_monthly_trends`)
   — reads the analytical CSV from `cleaned.dataset_path`, buckets rows by
   the calendar month of `order_purchase_timestamp`, and compares the last
   two months with data for `total_revenue`, `order_count`, and
   `average_review_score` (direction + % change). This is genuine
   time-series analysis, not just a snapshot check — it works today because
   the Olist data itself spans many months, not because the pipeline has
   been run multiple times.

Both feed `insight_generator.py`, which turns each evaluation/trend into an
`Insight` (`info` for healthy/increasing-or-flat, `warning` for
concerning/decreasing). `AnalysisResult.trends` nests the monthly trends
under `trends["monthly"]` to avoid colliding with the threshold-based keys
(both use KPI names like `average_review_score`).

**Caveat:** with the small 500-order sample, the most recent calendar month
is often partial (the sample's last order is 2018-08-26, not the 26th of a
full month), so the latest month-over-month comparison can look more
dramatic than it would against the full dataset in `data/raw/olist`.

## Key files
- `agent.py` — main agent entrypoint (`BIAnalystAgent`), called by the Orchestrator
- `trend_detection.py` — threshold-based KPI evaluation
- `monthly_trends.py` — real month-over-month trend detection from the analytical data
- `insight_generator.py` — turns evaluations/trends into human-readable insights

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [x] Implement threshold-based evaluation
- [x] Implement real month-over-month trend detection
- [x] Write unit tests against sample data in `data/sample/`
- [ ] Re-run against the full dataset in `data/raw/olist` to get trends
  unaffected by sample-size/partial-month noise

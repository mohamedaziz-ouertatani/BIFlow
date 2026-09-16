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
   two *complete* months with data for `total_revenue`, `order_count`, and
   `average_review_score` (direction + % change). This is genuine
   time-series analysis, not just a snapshot check — it works today because
   the Olist data itself spans many months, not because the pipeline has
   been run multiple times.

   A month is excluded from being "the latest month" if its order count is
   below 20% of the dataset's busiest month — this catches trailing
   stray/incomplete data (e.g. the real Olist dataset has exactly one order
   dated September 2018, long after volume effectively drops to zero in
   August; without this filter, that single order gets compared against a
   full August and produces a false "-100%" collapse in every metric).

Both feed `insight_generator.py`, which turns each evaluation/trend into an
`Insight` (`info` for healthy/increasing-or-flat, `warning` for
concerning/decreasing). `AnalysisResult.trends` nests the monthly trends
under `trends["monthly"]` to avoid colliding with the threshold-based keys
(both use KPI names like `average_review_score`).

**Verified against the full dataset** (`data/raw/olist`, ~99k orders):
after the trailing-month fix, July→August 2018 shows realistic trends
(-3.3% revenue, +2.9% order volume, +0.1% review score) instead of the
false collapse. With the small 500-order sample, the most recent calendar
month can still look noisier than the full data (it's a random subset, and
the sample's last order is 2018-08-26 — a partial day, not excluded by the
order-count filter since 500 random orders don't show an obvious volume
drop the way the real trailing stray order does).

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
- [x] Re-run against the full dataset in `data/raw/olist` and fix the
  trailing-stray-order false-collapse bug it surfaced
- [x] Support a second business domain (`banking`, Berka dataset) — see
  `docs/superpowers/specs/2026-09-16-multi-domain-banking-design.md`

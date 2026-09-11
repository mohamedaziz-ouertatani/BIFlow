# BI Semantic & KPI Agent

**Owner:** Person B

## Purpose
Defines the KPIs relevant to the business domain and computes their values
against the analytical dataset produced by the Data Engineering Agent. Its
output is the semantic layer the BI Analyst Agent builds insights on top of.

## Input
`shared.schemas.data_contracts.CleanedDataset` — `dataset_path` points at the
order-item-level analytical CSV written by the Data Engineering Agent.

## Output
`shared.schemas.data_contracts.KPICatalog` — 5 e-commerce KPIs (see
[`docs/kpi_catalog.md`](../../docs/kpi_catalog.md)): `total_revenue`,
`average_order_value`, `order_count`, `average_review_score`,
`on_time_delivery_rate`.

## Key files
- `agent.py` — main agent entrypoint (`KPISemanticAgent`), called by the Orchestrator
- `kpi_definitions.py` — KPI definitions per business domain
- `kpi_computation.py` — computes KPI values from the analytical table

## Note on business_domain
`CleanedDataset` doesn't carry `business_domain` today, so `KPISemanticAgent`
defaults to `"e-commerce"` via its constructor. TODO (owner): thread
`business_domain` through the shared contracts if/when a second domain is
added.

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [x] Implement core logic
- [x] Write unit tests against sample data in `data/sample/`
- [ ] Add category/state KPI breakdowns (see `docs/kpi_catalog.md`)

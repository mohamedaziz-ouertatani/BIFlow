# BI Semantic & KPI Agent

**Owner:** Mohamed Aymen Hamzeoui

## Purpose
Defines the KPIs relevant to the business domain and computes their values
against the analytical dataset produced by the Data Engineering Agent. Its
output is the semantic layer the BI Analyst Agent builds insights on top of.

## Input
`shared.schemas.data_contracts.CleanedDataset` — `dataset_path` points at the
order-item-level analytical CSV written by the Data Engineering Agent, and
`business_domain` (carried through from `RawDatasetRef`) selects which KPI
definitions to use.

## Output
`shared.schemas.data_contracts.KPICatalog` — 5 e-commerce KPIs (see
[`docs/kpi_catalog.md`](../../docs/kpi_catalog.md)): `total_revenue`,
`average_order_value`, `order_count`, `average_review_score`,
`on_time_delivery_rate`. Each KPI's overall value is in `computed_values`;
its `category`/`state` breakdowns are in `breakdowns`.

## Key files
- `agent.py` — main agent entrypoint (`KPISemanticAgent`), called by the Orchestrator
- `kpi_definitions.py` — KPI definitions per business domain
- `kpi_computation.py` — computes KPI values from the analytical table

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [x] Implement core logic
- [x] Write unit tests against sample data in `data/sample/`
- [x] Thread `business_domain` through the shared contract (`CleanedDataset`)
  instead of defaulting it on the agent's constructor
- [x] Add category/state KPI breakdowns (see `docs/kpi_catalog.md`) —
  `KPICatalog.breakdowns`, computed by `kpi_computation.compute_kpi_breakdowns`
  (e-commerce: `category`, `state`; banking: `region`; telco: `contract`,
  `internet_service`)
- [x] Support a second business domain (`banking`, Berka dataset) — see
  `docs/superpowers/specs/2026-09-16-multi-domain-banking-design.md`

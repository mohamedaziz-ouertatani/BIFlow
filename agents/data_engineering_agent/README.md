# Data Engineering Agent

**Owner:** Person A

## Purpose
Profiles the raw Olist Brazilian E-Commerce dataset (8 related CSVs),
applies data-quality cleaning, and joins everything into one order-item-level
analytical table. It is the first agent in the pipeline and its output feeds
the KPI/Semantic Agent.

## Input
`shared.schemas.data_contracts.RawDatasetRef` — `dataset_path` points at a
directory containing the Olist CSVs (e.g. `data/sample/olist` or
`data/raw/olist`), not a single file, since Olist is a relational dataset.

## Output
`shared.schemas.data_contracts.CleanedDataset` (which embeds a `ProfilingReport`)
— `dataset_path` points at the written analytical CSV
(`data/processed/olist_orders_analytical.csv` by default).

## How it works
1. **Profile** (`profiler.py`): loads all 8 raw tables, profiles each
   (row/column counts, dtypes, missing-value ratios, duplicate rows,
   anomalies), and aggregates them into one `ProfilingReport` with
   `table_name.column_name`-prefixed keys.
2. **Clean** (`cleaner.py`): drops exact duplicate rows per table, parses
   timestamp/date columns, drops `order_items` rows with null/negative
   price, and fills missing `product_category_name` with `"unknown"`.
3. **ETL** (`etl.py`): joins the cleaned tables at order-item grain —
   `order_items` + `orders` + `customers` + aggregated `order_payments`
   (summed per order) + aggregated `order_reviews` (latest score per order)
   + `products` (with English category name) + `sellers` — and writes the
   result to CSV.

Geolocation is profiled but not joined in (it's a zip-code lookup table,
not order-linked at a useful grain).

## Key files
- `agent.py` — main agent entrypoint (`DataEngineeringAgent`), called by the Orchestrator
- `profiler.py` — per-table profiling + dataset-level aggregation
- `cleaner.py` — data-quality cleaning rules
- `etl.py` — table joins + analytical CSV output
- `tools/` — any LangChain/LangGraph tools this agent exposes (none yet)

## Local dev
```bash
pip install -r requirements.txt
pytest tests/
```

## TODO
- [x] Implement core logic (profiling, cleaning, ETL join against Olist sample)
- [x] Write unit tests against sample data in `data/sample/`
- [ ] Load the analytical table into Postgres (currently CSV-only; see
  `docker-compose.yml`'s `db` service)
- [ ] Revisit cleaning rules once run against the full dataset in `data/raw/olist`
  (the sample may not surface every data-quality issue)

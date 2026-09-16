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
   result to CSV. Optionally also loads it into Postgres (see below).

Geolocation is profiled but not joined in (it's a zip-code lookup table,
not order-linked at a useful grain).

## Postgres loading (opt-in)

`DataEngineeringAgent(database_url=...)` also loads the analytical table
into a Postgres table (`orders_analytical`, replacing it each run) via
`etl.load_to_postgres()`. This is **opt-in** — `database_url` defaults to
`None`, so `DataEngineeringAgent()` stays CSV-only unless a caller
explicitly passes one (e.g. `get_settings().database_url` from
`shared/config.py`). CSV remains the interchange format between agents;
Postgres is an additional sink for ad-hoc SQL access.

The `db` service in `docker-compose.yml` maps to host port **5433** (not
5432) to avoid clashing with a native Postgres install some dev machines
already have. From the host, connect with
`postgresql://biflow:biflow@localhost:5433/biflow`; from inside another
docker-compose container, use `postgresql://biflow:biflow@db:5432/biflow`.

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
- [x] Load the analytical table into Postgres (opt-in, see above)
- [x] Revisit cleaning rules once run against the full dataset in `data/raw/olist`
  (the sample may not surface every data-quality issue). Ran the full
  pipeline against `data/raw/olist` (1.55M rows across 8 tables) and found:
  - `orders.order_approved_at` was never parsed to `datetime` — the
    `date_cols` heuristic in `cleaner.py` only matched `"timestamp"` and
    `*_date` columns, missing this `*_at` column. Fixed by also matching
    `*_at` suffixes (checked against every column across all 8 tables —
    no false positives).
  - `geolocation` has 261,831 exact duplicate rows (~26% of the table) —
    already handled correctly by the existing generic `drop_duplicates()`
    step; not joined into the analytical table anyway.
  - `order_reviews.review_comment_title` (88.3%) and
    `review_comment_message` (58.7%) are mostly missing, but neither is
    used downstream (only `review_score` is joined), so no cleaning rule
    was added for them.
  - No null/negative prices in `order_items` on the full dataset (that
    rule exists for defense-in-depth but doesn't currently trigger).
- [x] Support a second business domain (`banking`, Berka dataset) — see
  `docs/superpowers/specs/2026-09-16-multi-domain-banking-design.md`

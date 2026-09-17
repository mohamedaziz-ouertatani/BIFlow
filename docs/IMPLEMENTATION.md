# BIFlow — Implementation Guide

This document explains, in detail, everything built in BIFlow: what each
piece does, why it's designed the way it is, the real bugs found along the
way, and how it all fits together. Where the root [`README.md`](../README.md)
tells you *how to run it*, this tells you *how it works*.

BIFlow is a multi-agent Business Intelligence pipeline: raw e-commerce data
goes in one end, and an explainable, interactive dashboard comes out the
other, with five independent "agents" and an orchestrator in between.

---

## 1. Architecture at a glance

```
RAW DATA (Olist CSVs)
   │
   ▼
[Orchestrator] ──coordinates──► all agents below, in sequence
   │
   ├─► Data Engineering Agent     — profile, clean, join, (optionally) load to Postgres
   │        │
   │        ▼
   ├─► BI Semantic & KPI Agent    — compute 5 KPIs from the analytical table
   │        │
   │        ▼
   ├─► BI Analyst Agent           — threshold checks + real month-over-month trends
   │        │
   │        ▼
   ├─► Dashboard Generator Agent  — build the layout JSON, serve it over HTTP
   │        │
   │        ▼
   └─► BI Auditor / XAI Agent     — validate, explain, produce a traceability log
```

Agents never call each other directly. Every hand-off is a validated
[Pydantic](https://docs.pydantic.dev/) model defined in
[`shared/schemas/data_contracts.py`](../shared/schemas/data_contracts.py),
and the Orchestrator is the only thing that calls agent code. This means
each agent can be tested, understood, and (in principle) redeployed
independently — the contracts are the seam.

A separate **Next.js frontend** (`frontend/`) polls the Dashboard Agent's
HTTP API every 5 seconds and renders what it gets back. It's the only part
of the system that isn't a Python agent.

---

## 2. The dataset

BIFlow ships against the real
[Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
dataset — a relational dataset (not a single flat file) covering ~99,000
real orders from 2016–2018 across 9 CSVs (orders, customers, order items,
payments, reviews, products, sellers, geolocation, and a category-name
translation table).

- **`data/sample/olist/`** — a committed 500-order subset (with full
  foreign-key closure across the related tables) so tests and local dev
  don't need the full dataset. ~516KB.
- **`data/raw/olist/`** — the full dataset, gitignored (not committed;
  ~121MB). Present locally if you've downloaded it.

Because Olist is relational, `RawDatasetRef.dataset_path` points at a
**directory** of CSVs, not a single file — a deliberate departure from
what a naive reading of the original skeleton might suggest.

---

## 3. Shared contracts

Every object that crosses an agent boundary is one of these Pydantic
models (`shared/schemas/data_contracts.py`):

| Model | Produced by | Consumed by | Key fields |
|---|---|---|---|
| `RawDatasetRef` | caller (CLI/orchestrator input) | Data Engineering Agent | `dataset_path`, `dataset_name`, `business_domain` |
| `ProfilingReport` | Data Engineering Agent (internal) | embedded in `CleanedDataset` | `n_rows`, `column_types`, `missing_values`, `anomalies`, ... |
| `CleanedDataset` | Data Engineering Agent | KPI Agent, BI Analyst, Auditor | `dataset_path` (the analytical CSV), `data_quality_report`, `business_domain` |
| `KPICatalog` | KPI/Semantic Agent | BI Analyst, Dashboard, Auditor | `kpis` (definitions), `computed_values` (name → value) |
| `AnalysisResult` | BI Analyst Agent | Dashboard, Auditor | `insights` (list of `Insight`), `trends` (dict) |
| `DashboardSpec` | Dashboard Agent | Auditor | `dashboard_url`, `visualizations`, `kpis_shown` |
| `AuditReport` | Auditor/XAI Agent | final output | `validation_status`, `explanations`, `traceability_log` |

`shared/config.py` centralizes environment-based settings —
`get_settings().database_url` reads `DATABASE_URL` from the environment,
defaulting to a host-side Postgres connection string
(`postgresql://biflow:biflow@localhost:5433/biflow`) so it works the same
whether you're inside a container or running on the host.

`business_domain` is a good example of the contract discipline this
project follows: it was originally only known to `RawDatasetRef`, so the
KPI Agent had to default it to `"e-commerce"` — a real TODO. Instead of
letting that default silently paper over the gap, `CleanedDataset` was
extended to carry `business_domain` through explicitly, and the KPI Agent
now reads it from there. Every place that constructed a `CleanedDataset`
directly (agent code and tests) had to be updated — the kind of
ripple a shared contract change is supposed to force you to confront.

---

## 4. Data Engineering Agent

**Files:** `agents/data_engineering_agent/{agent,profiler,cleaner,etl}.py`

Takes a `RawDatasetRef` pointing at a directory of Olist CSVs and produces
one order-item-level analytical table.

1. **Profile** (`profiler.py`) — loads all 8 raw tables (geolocation
   included), profiles each individually (row/column counts, dtypes,
   missing-value ratios, duplicate rows, generic anomaly flags like "column
   X has >50% missing values"), then aggregates all of it into one
   `ProfilingReport` using `table_name.column_name`-prefixed keys so
   nothing collides across tables.
2. **Clean** (`cleaner.py`) — per table: drops exact duplicate rows, parses
   timestamp/date columns to real `datetime`, drops `order_items` rows with
   null/negative `price`, and fills missing `product_category_name` with
   `"unknown"`. Every rule that actually changes something appends a
   human-readable line to `transformations_applied`.
3. **ETL** (`etl.py`) — joins the cleaned tables at **order-item grain**:
   `order_items` + `orders` + `customers` + aggregated `order_payments`
   (summed per order, since an order can have multiple payment
   installments) + aggregated `order_reviews` (latest review per order,
   since a handful of orders have more than one) + `products` (joined
   against the category-name translation table for an English name) +
   `sellers`. Geolocation is profiled but deliberately **not** joined in —
   it's a zip-code lookup table, not meaningfully order-linked.
   Writes the result to `data/processed/analytical_table.csv` (the default
   output path, shared across business domains — see below).

### Postgres loading (opt-in)

`etl.py` also has `load_to_postgres()`, wired in as an **optional**
parameter on `run_etl()` / `DataEngineeringAgent(database_url=...)`. It
loads the same analytical table into a Postgres table (`orders_analytical`,
replaced on every run) via SQLAlchemy, *in addition to* the CSV — the CSV
remains the interchange format between agents, Postgres is an extra sink
for ad-hoc SQL access.

This is deliberately **opt-in** (`database_url` defaults to `None`):
making it automatic would have coupled every other agent's tests to a live
Postgres instance just because they happen to construct a
`DataEngineeringAgent`. The CLI (`python -m orchestrator`) turns it on by
default since that's a "real run," not a test.

---

## 5. BI Semantic & KPI Agent

**Files:** `agents/kpi_semantic_agent/{agent,kpi_definitions,kpi_computation}.py`

Defines and computes 5 KPIs for the `e-commerce` domain (see
[`docs/kpi_catalog.md`](kpi_catalog.md) for full formulas):

| KPI | What it measures |
|---|---|
| `total_revenue` | Sum of `price` for non-canceled order items |
| `average_order_value` | `total_revenue` ÷ non-canceled order count |
| `order_count` | Distinct orders, all statuses |
| `average_review_score` | Mean review score (1–5) |
| `on_time_delivery_rate` | Share of delivered orders arriving on/before the estimate |

`get_kpi_definitions(business_domain)` looks up KPI definitions before the
(potentially large) analytical CSV is ever read — an unknown domain fails
fast with a `KeyError` instead of after an unnecessary file read.

---

## 6. BI Analyst Agent

**Files:** `agents/bi_analyst_agent/{agent,trend_detection,monthly_trends,insight_generator}.py`

This is the most conceptually interesting agent, because "trend
detection" turned out to mean two genuinely different things once actually
built:

### 6.1 Threshold evaluation (`trend_detection.py`)

The agent receives a single `KPICatalog` **snapshot** — there's no
built-in history to compare across runs. So for the two KPIs with a
natural business threshold (`on_time_delivery_rate` ≥ 0.9,
`average_review_score` ≥ 4.0), it just flags `"healthy"` or `"concerning"`.
The other three KPIs (revenue, AOV, order count) have no natural
threshold and aren't evaluated this way.

### 6.2 Real month-over-month trends (`monthly_trends.py`)

This is genuine time-series analysis: it reads the underlying analytical
CSV (via the newer `BIAnalystAgent.run(cleaned, kpis)` signature — it now
takes `CleanedDataset` too, not just `KPICatalog`), buckets rows by the
calendar month of `order_purchase_timestamp`, and computes real
direction + % change for `total_revenue`, `order_count`, and
`average_review_score` between the last two *complete* months. It keeps
the **full per-month series** (not just the two-point comparison) so the
frontend can render a proper trend line, not just a before/after bar.

**A real bug this surfaced:** running against the full ~99k-order dataset
initially showed every metric "collapsing -100%." The cause: the real
Olist dataset has exactly one straggler order dated September 2018, long
after volume effectively drops to zero in August. The naive "last two
months" logic compared that single order against a full August and got a
nonsensical result. Fixed by excluding any month whose order count is
below 20% of the dataset's busiest month before picking the comparison
window — a ratio-based rule so it adapts to both the 500-order sample and
the full ~99k-order dataset without a hardcoded absolute count.

### 6.3 Insights (`insight_generator.py`)

Turns both kinds of trend into `Insight` objects: `info` severity for
healthy/increasing-or-flat, `warning` for concerning/decreasing.
`AnalysisResult.trends` nests the monthly-trend dict under a `"monthly"`
key specifically to avoid colliding with the threshold-based keys (both
use names like `average_review_score`).

---

## 7. Dashboard Generator Agent

**Files:** `agents/dashboard_agent/{agent,layout_builder,api}.py`

1. **`layout_builder.build_layout(analysis, kpis)`** — builds one
   JSON-serializable layout: `kpi_cards` (one per KPI: name, label,
   value), `insights` (one per `Insight`: title, description, severity),
   and `monthly_trends` (metric name → list of `{month, value}` points,
   pulled straight from `analysis.trends["monthly"]`).
2. **`DashboardAgent.run(analysis, kpis)`** — builds the layout, writes it
   to `data/processed/dashboard_layout.json`, and returns a
   `DashboardSpec`.
3. **`api.py`** — a small FastAPI app (`GET /api/dashboard`,
   `GET /api/health`) that reads that JSON file and serves it over HTTP,
   with CORS open for the frontend's origin.

This used to be a **Streamlit** app (`app.py`, since removed) that
re-rendered the layout server-side on every page load. It's now a pure
JSON API — the frontend owns rendering, polling, and all UI state.

---

## 8. Frontend (Next.js)

**Directory:** `frontend/` (App Router, TypeScript, no Tailwind)

`src/app/page.tsx` is a client component that polls
`GET {NEXT_PUBLIC_API_URL}/api/dashboard` every 5 seconds and renders:

- A grid of KPI cards
- One `TrendChart` (Recharts line chart) per metric in `monthly_trends`
- A severity-colored insights list
- Loading / "no data yet" (404) / error (API unreachable) states

**Important detail:** `NEXT_PUBLIC_API_URL` is read **client-side, in the
browser**, not inside the Docker network. When running via
`docker-compose`, it must point at a host-reachable address
(`http://localhost:8000`, matching the API's exposed port) — never the
internal `dashboard_agent` service name, which the browser can't resolve.

### Testing

Jest + React Testing Library (`page.test.tsx`, `TrendChart.test.tsx`),
run via `next/jest` with a `ResizeObserver` polyfill (Recharts'
`ResponsiveContainer` needs it; jsdom doesn't implement it). These tests
mock `global.fetch` — a deliberate, standard frontend practice, not a
departure from the Python side's "no mocks" philosophy: the backend's real
behavior (Postgres, HTTP, the full pipeline) is already covered by
`pytest`, so the frontend tests only need to prove *rendering* is correct
given a response shape, including a fake-timers test that proves the poll
genuinely re-fires after 5 seconds.

---

## 9. BI Auditor / XAI Agent

**Files:** `agents/auditor_xai_agent/{agent,validators,explainer}.py`

The last stage. Takes everything every prior stage produced and:

1. **`validators.validate_pipeline_outputs(cleaned, kpis, analysis)`** —
   `"failed"` if zero rows were profiled; `"passed_with_warnings"` if the
   cleaning report has data-quality anomalies *or* any insight has
   `warning`/`critical` severity; `"passed"` otherwise.
2. **`explainer.generate_explanations(kpis, analysis)`** — one explanation
   per KPI (its description + formula + rounded computed value) and one
   per insight (its description) — assembled entirely from data already on
   hand, no new computation.
3. **`agent.py`** — wires both together plus a `traceability_log`
   **synthesized** from the four objects it receives (row counts,
   transformation count, KPI/insight counts, dashboard URL) — there's no
   separate execution-trace object being threaded through; the Auditor
   infers what happened from the shape of what it was handed.

---

## 10. Orchestrator

**Files:** `orchestrator/{orchestrator,__main__}.py`

`BIFlowOrchestrator.run_pipeline(raw_dataset)` calls all five agents
**directly, in-process** (not over HTTP/RPC) in sequence, threading the
right contract objects between them. `analytical_path`,
`dashboard_layout_path`, and `database_url` are constructor parameters
(all optional) so tests can redirect output to a temp directory and stay
Postgres-free unless they explicitly opt in.

### CLI (`python -m orchestrator`)

```bash
python -m orchestrator <dataset_path> <business_domain> [options]
```

Runs the pipeline for real, prints the validation status, traceability
log, and every explanation, and exits `1` if `validation_status ==
"failed"` (else `0`). Unlike the library-level orchestrator, **the CLI
loads into Postgres by default** (`--no-postgres` to opt out) — it's the
"real run" entrypoint, not a test.

**Design note:** because the Orchestrator imports every agent class
directly (rather than calling them as separate services), its Docker image
needs every agent's runtime dependencies (pandas, streamlit-turned-fastapi,
sqlalchemy, psycopg2) installed too. This surfaced as a real bug: the
orchestrator container failed with `ModuleNotFoundError: No module named
'pandas'` the first time it actually tried to run the pipeline, because its
own `requirements.txt` only had what *orchestrator.py itself* imports, not
what it transitively needs from every agent it instantiates. Fixed by
adding the transitive deps. A distributed version of this system (agents
as separate services called over RPC) would need a different
dependency/build story entirely.

---

## 11. Infrastructure

### Docker Compose

One service per agent + orchestrator + `frontend` + Postgres (`db`).
Python services bind-mount the repo (`.:/app`) so code changes take effect
without a rebuild; the `frontend` service does **not** (it has its own
`COPY` in the Dockerfile), so frontend changes need
`docker-compose up -d --build frontend`.

**A real bug this surfaced:** the `db` service originally mapped host port
5432 → container 5432. On this dev machine, a native (non-Docker) Postgres
install was already listening on 5432, silently intercepting connections
before they reached the container. Remapped to **5433:5432** — a safer
default for any dev machine that might have a local Postgres install.

### CI (GitHub Actions, `.github/workflows/tests.yml`)

Two jobs, both on every push/PR to `main`:

- **`pytest`** — spins up a real `postgres:16` service container (not
  mocked), installs `requirements-dev.txt` plus every agent's own
  `requirements.txt`, runs the full Python suite.
- **`frontend`** — `npm ci`, `npm run lint`, `npm test -- --ci`,
  `npm run build`.

**Two real CI-only bugs found and fixed:**
1. CI runs the bare `pytest` command, which — unlike `python -m pytest` —
   doesn't add the repo root to `sys.path`. Since no `tests/` directory
   has an `__init__.py`, every `from agents...`/`from orchestrator...`
   import broke in CI while working locally. Fixed with `pyproject.toml`'s
   `pythonpath = ["."]`.
2. CI installed unpinned `pandas`, which resolved a newer version (3.0.5)
   that reports string-column dtype as `"str"` instead of `"object"` — a
   real behavioral difference from pandas 2.x. Pinned `pandas==2.3.3`
   everywhere it's required. The same category of issue happened again
   with unpinned `fastapi` resolving a broken prerelease `starlette`; fixed
   by pinning `fastapi==0.124.4` / `uvicorn==0.38.0` and adding the missing
   `httpx` test dependency.

Both were caught by actually watching CI runs rather than assuming a push
would pass — and both were reproduced locally (a clean venv matching CI's
exact install steps, and the bare `pytest` command) before being
considered fixed.

---

## 12. Testing philosophy

Every piece of business logic in this project was built test-first
(red → green, one behavior at a time), verified against **real data** — the
actual 500-order sample, and at full scale (~99k orders) — rather than
synthetic mocks wherever the code under test touches data, Postgres, or
HTTP. The one deliberate exception is the frontend's `fetch` mocking,
which is standard practice for testing UI rendering logic in isolation
from a backend that's already covered elsewhere.

Beyond automated tests, several features were also verified by actually
running them: loading the live dashboard in a browser and watching it
poll in real time, curling both API and frontend containers after a
`docker-compose` rebuild, and running the full CLI against both the
sample and the complete dataset.

**Current counts:** 71 Python tests (`pytest`), 6 frontend tests (`npm
test` in `frontend/`).

---

## 13. Known limitations / next steps

- **Single-process orchestrator** — agents are Python classes called
  in-process, not independent services communicating over a network. Fine
  for this project's scale; would need real service boundaries (HTTP/RPC,
  per-agent deployability) to scale further.
- **`execution_log.py` is unused** — the Auditor synthesizes its
  traceability log from each stage's output after the fact, rather than
  the Orchestrator logging step-by-step as it runs.
- **No retry/skip/halt logic** between pipeline stages — a failure in any
  agent currently just propagates as an unhandled exception.
- **Single business domain** — only `e-commerce` has KPI definitions.
  Multi-domain support was designed for (`business_domain` flows through
  the contracts cleanly) but never proven with a second domain.
- **No end-to-end (Playwright) frontend tests** — only unit-level
  rendering tests with a mocked API.

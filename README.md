# BIFlow — Multi-Agent BI Pipeline

BIFlow is a multi-agent system that automates a Business Intelligence
pipeline from raw data to an explainable, interactive dashboard.

## Architecture

```
RAW DATA
   |
   v
[Orchestrator Agent] --coordinates--> all agents below
   |
   +-> [Data Engineering Agent]   (Profiling + Quality/Cleaning + ETL)
   |        |
   |        v
   +-> [BI Semantic & KPI Agent]   (KPI definitions, formulas)
   |        |
   |        v
   +-> [BI Analyst Agent]          (Trends, anomalies, insights)
   |        |
   |        v
   +-> [Dashboard Generator Agent] (Interactive dashboard)
   |        |
   |        v
   +-> [BI Auditor / XAI Agent]    (Validation, explanations, traceability)
```

Each agent communicates with the Orchestrator only — agents do not call
each other directly. The Orchestrator passes validated Pydantic objects
(see `shared/schemas/data_contracts.py`) between agents and logs every step
for the Auditor/XAI agent to consume.

See [`docs/architecture.md`](docs/architecture.md) for more detail.

## Team assignment

| Agent | Owner |
|---|---|
| Data Engineering Agent (Profiler + Cleaning + ETL) | Person A |
| BI Semantic & KPI Agent | Person B |
| BI Analyst Agent | Person C |
| Dashboard Generator Agent | Person D |
| BI Auditor/XAI Agent + Orchestrator | Person E |

## Repository layout

- `orchestrator/` — coordinates the pipeline across all agents
- `agents/` — one folder per agent, each independently runnable/testable
- `shared/` — shared Pydantic schemas, config, and utils used by all components
- `data/` — raw/processed data (gitignored) and a committed sample dataset
- `docs/` — architecture notes, KPI catalog, report templates
- `tests/` — end-to-end integration test for the full pipeline

## Getting started

```bash
pip install -r requirements-dev.txt
docker-compose up
```

Each agent also has its own `requirements.txt` and `tests/` — see that
agent's `README.md` for local dev instructions.

## Dataset

BIFlow uses the [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
dataset (`business_domain="e-commerce"`):

- `data/raw/olist/` — full dataset (gitignored, not committed)
- `data/sample/olist/` — small committed subset (500 orders + related rows)
  for local dev and tests — see [`data/sample/README.md`](data/sample/README.md)

## Status

All 5 agents and the Orchestrator are implemented and wired end-to-end
against the Olist sample data — `BIFlowOrchestrator().run_pipeline(raw_dataset)`
runs the full pipeline and returns a real `AuditReport`. Run `pytest` from
the repo root, or `streamlit run agents/dashboard_agent/app.py` after
running the pipeline once to see the dashboard. CI runs the full suite
(including real-Postgres tests) on every push/PR to `main` — see
[`.github/workflows/tests.yml`](.github/workflows/tests.yml).

Postgres loading is wired in but **opt-in**: pass `database_url` to
`BIFlowOrchestrator`/`DataEngineeringAgent` to also load the analytical
table into the `db` service's Postgres (see
[`agents/data_engineering_agent/README.md`](agents/data_engineering_agent/README.md#postgres-loading-opt-in)
for the host-vs-container connection details, including the port 5433 remap).

## Next steps

1. ~~Scaffold the skeleton~~ — done.
2. ~~Add a small sample dataset to `data/sample/`~~ — done, using Olist.
3. ~~Get `docker-compose up` running with all stub services~~ — done.
4. ~~Implement all 5 agents + Orchestrator wiring~~ — done.
5. ~~Load the Data Engineering Agent's analytical table into Postgres~~ — done, opt-in.
6. ~~Replace threshold-only "trend detection" with real time-series analysis~~
   — done: `BIAnalystAgent` now buckets the analytical table by calendar
   month and detects genuine month-over-month trends (see
   `agents/bi_analyst_agent/README.md`).
7. ~~Thread `business_domain` through the shared contracts~~ — done:
   `CleanedDataset` now carries `business_domain` from `RawDatasetRef`, and
   `KPISemanticAgent` reads it from there instead of a constructor default.
8. Make Postgres loading the actual default for real (non-test) pipeline
   runs, e.g. via a CLI entrypoint that passes `get_settings().database_url`.
9. ~~Re-run the pipeline against the full dataset in `data/raw/olist`~~ —
   done: runs cleanly in ~9s on ~99k orders, and surfaced a real bug (a
   single trailing stray order in September 2018 made trend detection
   report a false "-100%" collapse) — fixed by excluding months whose
   order count is far below typical volume (see
   `agents/bi_analyst_agent/README.md`).

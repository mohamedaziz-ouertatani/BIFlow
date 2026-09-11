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

## Next steps

1. Each owner fills in their agent's `README.md` and confirms/adjusts their
   input/output schema in `shared/schemas/data_contracts.py` (open a PR if
   changing a shared contract).
2. Add a small sample dataset to `data/sample/` so the end-to-end test can
   run against something real before full datasets are ready.
3. Get `docker-compose up` running with all stub services before writing
   real logic, so integration issues surface early.

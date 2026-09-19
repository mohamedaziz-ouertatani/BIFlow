# BIFlow Architecture

How the pieces fit together. For the per-component detail (contracts, bugs
found, testing philosophy) see [`IMPLEMENTATION.md`](IMPLEMENTATION.md).

## Pipeline

```
RAW DATA
   |
   v
[Orchestrator Agent] --coordinates--> all agents below
   |
   +-> [Data Engineering Agent]   (Profiling + Quality/Cleaning + ETL)
   +-> [BI Semantic & KPI Agent]   (KPI definitions, formulas)
   +-> [BI Analyst Agent]          (Trends, anomalies, insights)
   +-> [Dashboard Generator Agent] (Interactive dashboard)
   +-> [BI Auditor / XAI Agent]    (Validation, explanations, traceability)
```

## Principles

- Agents communicate with the Orchestrator only — never directly with each other.
- All hand-offs are validated Pydantic models defined in
  `shared/schemas/data_contracts.py`.
- Every pipeline stage is logged (`shared/schemas/execution_trace.py`) so the
  Auditor/XAI agent can reconstruct and explain the full run.

## Runtime topology

The agents are **library modules called in-process** by the orchestrator, not
separate services. The only long-running processes are:

- **`dashboard_agent`** (FastAPI, port 8000) — serves the dashboard layout,
  drill-down rows, the PDF report and NL query, and runs the pipeline on
  demand (`GET /api/pipeline/run`, streamed as Server-Sent Events). It
  imports the orchestrator, so it carries every agent's dependencies.
- **`frontend`** (Next.js, port 3000) — the landing console and the
  Telemetry Wall dashboard, talking to the API from the browser.
- **`db`** (Postgres, host port 5433) — optional sink for the analytical
  table; the CSV in `data/processed/` remains the interchange format.

## Decisions

- **Stage failures halt the run.** Each stage's output feeds the next, so
  there is nothing meaningful to retry or skip to. The orchestrator
  re-raises the first failure as `PipelineStageError` naming the stage, and
  records started/succeeded/failed events in an `ExecutionTrace`.
- **KPI definitions are versioned by git, per domain.** They live in code
  (`kpi_definitions.py`, and `row_filters.py` for the row-level filters),
  keyed by `business_domain` and looked up with `get_kpi_definitions`. There
  is no separate runtime version field: a change to a KPI's formula is a
  code change, reviewed like any other. Revisit this if definitions ever
  need to change per customer or be pinned to a past report.
- **LLM use is limited to NL query, and it is local.** Insights, threshold
  checks and explanations are rule-based and templated, so no cloud LLM
  provider is involved anywhere. The dashboard's natural-language box calls
  a local Ollama server (`OLLAMA_URL`, default model `qwen2.5:3b`) so no
  data leaves the machine; it answers only from the dashboard layout.

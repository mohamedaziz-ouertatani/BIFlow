# BIFlow Architecture

TODO (owner, Person E): expand this document as the system solidifies.

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

## Open questions

- TODO: retry/skip/halt policy when a stage fails
- TODO: how KPI definitions are versioned across business domains
- TODO: LLM provider/model choice for insight generation and explanations

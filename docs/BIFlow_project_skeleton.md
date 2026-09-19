# BIFlow — Multi-Agent BI Pipeline: Project Skeleton

## Instructions for Claude Code

Use this document to scaffold the initial repository structure for **BIFlow**, a multi-agent
system that automates a Business Intelligence pipeline from raw data to an explainable
interactive dashboard. Create the folder structure, stub files, and interface contracts
described below so that 5 team members can each start building their agent independently,
in parallel, without blocking on each other.

Do not implement business logic yet — only create the skeleton: folders, empty/stub files,
class and function signatures, docstrings, `README.md` per component, and dependency files.
Each stub should raise `NotImplementedError` (or the language equivalent) where logic goes,
with a comment describing what the owner needs to implement.

---

## 1. Tech stack

- **Language:** Python 3.11+ for all agents and the orchestrator
- **Agent framework:** LangGraph (preferred) or LangChain for agent/LLM orchestration
- **Data:** Pandas / Polars, SQL (PostgreSQL for the data model)
- **Inter-agent contracts:** Pydantic models (shared schemas, versioned)
- **Dashboard:** Streamlit or Plotly Dash for MVP (can be swapped for a Next.js frontend later)
- **Containerization:** Docker + docker-compose, one service per agent + orchestrator + dashboard
- **Testing:** pytest, one test folder per agent

---

## 2. High-level architecture

```
RAW DATA
   │
   ▼
[Orchestrator Agent] ──coordinates──> all agents below
   │
   ├─► [Data Engineering Agent]   (Profiling + Quality/Cleaning + ETL)
   │        │
   │        ▼
   ├─► [BI Semantic & KPI Agent]   (KPI definitions, formulas)
   │        │
   │        ▼
   ├─► [BI Analyst Agent]          (Trends, anomalies, insights)
   │        │
   │        ▼
   ├─► [Dashboard Generator Agent] (Interactive dashboard)
   │        │
   │        ▼
   └─► [BI Auditor / XAI Agent]    (Validation, explanations, traceability)
```

Each agent communicates with the Orchestrator only — agents do not call each other directly.
The Orchestrator passes validated Pydantic objects between agents and logs every step for
the Auditor/XAI agent to consume.

---

## 3. Repository structure to create

```
biflow/
├── README.md
├── docker-compose.yml
├── .env.example
├── requirements-dev.txt
│
├── orchestrator/
│   ├── README.md
│   ├── orchestrator.py
│   ├── execution_log.py
│   ├── requirements.txt
│   └── tests/
│       └── test_orchestrator.py
│
├── agents/
│   ├── data_engineering_agent/
│   │   ├── README.md
│   │   ├── agent.py
│   │   ├── profiler.py
│   │   ├── cleaner.py
│   │   ├── etl.py
│   │   ├── tools/
│   │   │   └── __init__.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_data_engineering_agent.py
│   │
│   ├── kpi_semantic_agent/
│   │   ├── README.md
│   │   ├── agent.py
│   │   ├── kpi_definitions.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_kpi_semantic_agent.py
│   │
│   ├── bi_analyst_agent/
│   │   ├── README.md
│   │   ├── agent.py
│   │   ├── trend_detection.py
│   │   ├── insight_generator.py
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_bi_analyst_agent.py
│   │
│   ├── dashboard_agent/
│   │   ├── README.md
│   │   ├── agent.py
│   │   ├── layout_builder.py
│   │   ├── app.py                 # Streamlit/Dash entrypoint
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_dashboard_agent.py
│   │
│   └── auditor_xai_agent/
│       ├── README.md
│       ├── agent.py
│       ├── validators.py
│       ├── explainer.py
│       ├── requirements.txt
│       └── tests/
│           └── test_auditor_xai_agent.py
│
├── shared/
│   ├── __init__.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── data_contracts.py      # Pydantic models exchanged between agents
│   │   └── execution_trace.py     # Shared log/trace schema for the Orchestrator + Auditor
│   ├── config.py
│   └── utils/
│       └── __init__.py
│
├── data/
│   ├── raw/                       # input datasets (gitignored)
│   ├── processed/                 # cleaned/ETL output (gitignored)
│   └── sample/                    # small sample dataset committed for dev/testing
│
├── docs/
│   ├── architecture.md
│   ├── kpi_catalog.md             # filled in by kpi_semantic_agent owner
│   ├── data_quality_report_template.md
│   └── xai_report_template.md
│
└── tests/
    └── test_end_to_end.py         # integration test running the full pipeline on sample data
```

---

## 4. Shared data contracts (`shared/schemas/data_contracts.py`)

Create Pydantic models for every hand-off between agents. Stub these with fields and
docstrings — fields marked `# TODO: confirm with <agent owner>` should stay flexible until
the owning agent's implementation solidifies them.

```python
# shared/schemas/data_contracts.py

from pydantic import BaseModel
from typing import Any

class RawDatasetRef(BaseModel):
    """Input handed to the Data Engineering Agent."""
    dataset_path: str
    dataset_name: str
    business_domain: str  # e.g. "e-commerce", "banking"

class ProfilingReport(BaseModel):
    """Output of the profiling step, input to cleaning."""
    n_rows: int
    n_columns: int
    column_types: dict[str, str]
    missing_values: dict[str, float]
    duplicate_rows: int
    anomalies: list[str]

class CleanedDataset(BaseModel):
    """Output of the Data Engineering Agent, input to KPI agent."""
    dataset_path: str
    data_quality_report: ProfilingReport
    transformations_applied: list[str]

class KPIDefinition(BaseModel):
    """One KPI as defined by the KPI/Semantic Agent."""
    name: str
    formula: str
    description: str
    dimensions: list[str]

class KPICatalog(BaseModel):
    """Output of the KPI/Semantic Agent, input to BI Analyst."""
    kpis: list[KPIDefinition]
    computed_values: dict[str, Any]

class Insight(BaseModel):
    """One insight/recommendation from the BI Analyst Agent."""
    title: str
    description: str
    related_kpi: str
    severity: str  # e.g. "info", "warning", "critical"

class AnalysisResult(BaseModel):
    """Output of the BI Analyst Agent, input to Dashboard Agent."""
    insights: list[Insight]
    trends: dict[str, Any]

class DashboardSpec(BaseModel):
    """Output of the Dashboard Generator Agent, input to Auditor/XAI."""
    dashboard_url: str
    visualizations: list[str]
    kpis_shown: list[str]

class AuditReport(BaseModel):
    """Final output of the Auditor/XAI Agent."""
    validation_status: str
    explanations: dict[str, str]
    traceability_log: list[str]
```

---

## 5. Orchestrator interface (`orchestrator/orchestrator.py`)

Stub a class with one method per pipeline stage, plus a `run_pipeline` entrypoint. Include
a docstring on each method describing what decision logic the owner needs to add (retries,
skip conditions, validation between steps).

```python
# orchestrator/orchestrator.py

from shared.schemas.data_contracts import (
    RawDatasetRef, CleanedDataset, KPICatalog, AnalysisResult, DashboardSpec, AuditReport
)

class BIFlowOrchestrator:
    """
    Coordinates the BIFlow pipeline across all agents.

    TODO (owner): implement dynamic routing, error handling (retry/skip/halt),
    and full execution logging for the Auditor/XAI agent.
    """

    def run_pipeline(self, raw_dataset: RawDatasetRef) -> AuditReport:
        """Runs the full pipeline end-to-end and returns the final audit report."""
        cleaned = self._run_data_engineering(raw_dataset)
        kpis = self._run_kpi_semantic(cleaned)
        analysis = self._run_bi_analyst(kpis)
        dashboard = self._run_dashboard(analysis, kpis)
        return self._run_auditor(cleaned, kpis, analysis, dashboard)

    def _run_data_engineering(self, raw_dataset: RawDatasetRef) -> CleanedDataset:
        raise NotImplementedError("TODO: call Data Engineering Agent")

    def _run_kpi_semantic(self, cleaned: CleanedDataset) -> KPICatalog:
        raise NotImplementedError("TODO: call KPI/Semantic Agent")

    def _run_bi_analyst(self, kpis: KPICatalog) -> AnalysisResult:
        raise NotImplementedError("TODO: call BI Analyst Agent")

    def _run_dashboard(self, analysis: AnalysisResult, kpis: KPICatalog) -> DashboardSpec:
        raise NotImplementedError("TODO: call Dashboard Generator Agent")

    def _run_auditor(self, cleaned, kpis, analysis, dashboard) -> AuditReport:
        raise NotImplementedError("TODO: call Auditor/XAI Agent")
```

---

## 6. Per-agent `README.md` template

Generate a `README.md` in each agent folder using this template, filled in with that
agent's specific purpose/inputs/outputs from the contracts above:

```markdown
# <Agent Name>

**Owner:** <team member name>

## Purpose
<one paragraph — what this agent does and why it exists in the pipeline>

## Input
<Pydantic model(s) from shared/schemas/data_contracts.py this agent consumes>

## Output
<Pydantic model(s) this agent produces>

## Key files
- `agent.py` — main agent entrypoint, called by the Orchestrator
- <other files specific to this agent>

## Local dev
\`\`\`bash
pip install -r requirements.txt
pytest tests/
\`\`\`

## TODO
- [ ] Implement core logic
- [ ] Write unit tests against sample data in `data/sample/`
- [ ] Document any LLM prompts used in `prompts/` (create if needed)
```

---

## 7. Team assignment (for reference — put in root `README.md`)

| Agent | Owner |
|---|---|
| Data Engineering Agent (Profiler + Cleaning + ETL) | Mohamed Aziz Ouertatani |
| BI Semantic & KPI Agent | Mohamed Aymen Hamzeoui |
| BI Analyst Agent | Mohamed Aymen Hamzeoui |
| Dashboard Generator Agent | Mohamed Aziz Ouertatani |
| BI Auditor/XAI Agent | Mohamed Aymen Hamzeoui |
| Frontend | Mohamed Aziz Ouertatani |
| Orchestrator | Mohamed Aziz Ouertatani & Mohamed Aymen Hamzeoui |

## 8. Immediate next steps after scaffolding

1. Each owner fills in their agent's `README.md` and confirms/adjusts their input/output
   schema in `shared/schemas/data_contracts.py` (open a PR if changing a shared contract).
2. Add a small sample dataset to `data/sample/` so the end-to-end test can run against
   something real before full datasets are ready.
3. Get `docker-compose up` running with all stub services before writing real logic, so
   integration issues surface early.

# Auditor/XAI drill-down in the dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let a user click any KPI card or insight in the dashboard and see the actual analytical-table rows that produced it, alongside a plain-text trace of the formula/filter/row-count.

**Architecture:** A new `row_filters.py` module in `kpi_semantic_agent` defines each KPI's row-level filter once, reused by both the existing aggregate KPI computation (refactored to call it) and a new `GET /api/drilldown` endpoint. The frontend gets a new lazy-loading `DrillDownPanel` component mounted from both the existing KPI-detail panel and a newly-interactive Insights tab.

**Tech Stack:** Python (FastAPI, pandas, pydantic), TypeScript/React (Next.js), Jest + React Testing Library, pytest.

**Spec:** [docs/superpowers/specs/2026-09-18-auditor-drilldown-design.md](../specs/2026-09-18-auditor-drilldown-design.md)

## Global Constraints

- One definition per KPI's row filter — `row_filters.py` is the single source of truth; `kpi_computation.py` must call it, never re-inline the same condition.
- Drill-down endpoint caps returned rows at 50 (`DRILLDOWN_ROW_LIMIT = 50`), always reporting `total_rows` alongside the capped `rows`.
- Breakdown-tab (per-category/region bar) drill-down is explicitly out of scope for this plan.
- No new query params beyond `domain`, `kpi`, `month` on `/api/drilldown`.

---

## Task 1: `Insight.month` field + monthly-trend insight generation

**Files:**
- Modify: `shared/schemas/data_contracts.py:66-72` (`Insight` class)
- Modify: `agents/bi_analyst_agent/insight_generator.py:114-121` (inside `generate_monthly_trend_insights`)
- Test: `agents/bi_analyst_agent/tests/test_insight_generator_monthly.py`

**Interfaces:**
- Produces: `Insight.month: str | None` (default `None`) — the `YYYY-MM` a monthly-trend insight is about, `None` for threshold insights and insights with no time dimension.

- [ ] **Step 1: Write the failing test**

Add to `agents/bi_analyst_agent/tests/test_insight_generator_monthly.py`:

```python
def test_generate_monthly_trend_insights_sets_month_to_the_latest_month():
    monthly_trends = {
        "total_revenue": {
            "previous_month": "2018-01",
            "latest_month": "2018-02",
            "previous_value": 100.0,
            "latest_value": 150.0,
            "pct_change": 50.0,
            "direction": "increasing",
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert insights[0].month == "2018-02"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest agents/bi_analyst_agent/tests/test_insight_generator_monthly.py::test_generate_monthly_trend_insights_sets_month_to_the_latest_month -v`
Expected: FAIL — `AttributeError: 'Insight' object has no attribute 'month'`

- [ ] **Step 3: Add the field to `Insight`**

In `shared/schemas/data_contracts.py`, change:

```python
class Insight(BaseModel):
    """One insight/recommendation from the BI Analyst Agent."""

    title: str
    description: str
    related_kpi: str
    severity: str  # e.g. "info", "warning", "critical"
```

to:

```python
class Insight(BaseModel):
    """One insight/recommendation from the BI Analyst Agent."""

    title: str
    description: str
    related_kpi: str
    severity: str  # e.g. "info", "warning", "critical"
    # The YYYY-MM this insight is about, for monthly-trend insights (drives
    # the drill-down endpoint's month filter). None for threshold insights
    # and insights with no time dimension.
    month: str | None = None
```

- [ ] **Step 4: Set `month` in `generate_monthly_trend_insights`**

In `agents/bi_analyst_agent/insight_generator.py`, change the `Insight(...)` construction inside `generate_monthly_trend_insights` (around line 114-120) from:

```python
        insights.append(
            Insight(
                title=title,
                description=description,
                related_kpi=metric_name,
                severity=severity,
            )
        )
```

to:

```python
        insights.append(
            Insight(
                title=title,
                description=description,
                related_kpi=metric_name,
                severity=severity,
                month=trend["latest_month"],
            )
        )
```

Leave `generate_insights` (threshold insights, top of the file) and the
"no time dimension" insight (also in `generate_monthly_trend_insights`,
earlier `return [Insight(...)]` block) unchanged — both correctly default
`month` to `None`.

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest agents/bi_analyst_agent/tests/test_insight_generator_monthly.py -v`
Expected: all PASS, including the new test

- [ ] **Step 6: Run the full bi_analyst_agent suite to confirm nothing else broke**

Run: `python -m pytest agents/bi_analyst_agent/tests -q`
Expected: all PASS

- [ ] **Step 7: Commit**

```bash
git add shared/schemas/data_contracts.py agents/bi_analyst_agent/insight_generator.py agents/bi_analyst_agent/tests/test_insight_generator_monthly.py
git commit -m "Add Insight.month, set from monthly-trend insights"
```

---

## Task 2: Pass `month` through the dashboard layout

**Files:**
- Modify: `agents/dashboard_agent/layout_builder.py:60-67` (the `insights` list comprehension in `build_layout`)
- Test: `agents/dashboard_agent/tests/test_layout_builder.py:71-94`

**Interfaces:**
- Consumes: `Insight.month` (Task 1)
- Produces: each dict in the dashboard layout's `"insights"` list gains a `"month"` key, consumed by the frontend in Task 10.

- [ ] **Step 1: Update the existing test's expectation (this is also the failing-test step — the assertion is exact-equality, so it will fail until Step 3 lands)**

In `agents/dashboard_agent/tests/test_layout_builder.py`, change
`test_build_layout_includes_an_insight_entry_per_insight`'s assertion from:

```python
    assert layout["insights"] == [
        {
            "title": "Revenue dip in March",
            "description": "Revenue dropped 20% vs February",
            "related_kpi": "total_revenue",
            "severity": "warning",
        }
    ]
```

to:

```python
    assert layout["insights"] == [
        {
            "title": "Revenue dip in March",
            "description": "Revenue dropped 20% vs February",
            "related_kpi": "total_revenue",
            "severity": "warning",
            "month": None,
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest agents/dashboard_agent/tests/test_layout_builder.py::test_build_layout_includes_an_insight_entry_per_insight -v`
Expected: FAIL — actual dict has no `"month"` key yet

- [ ] **Step 3: Add `month` to the layout builder**

In `agents/dashboard_agent/layout_builder.py`, change:

```python
    insights = [
        {
            "title": insight.title,
            "description": insight.description,
            "related_kpi": insight.related_kpi,
            "severity": insight.severity,
        }
        for insight in analysis.insights
    ]
```

to:

```python
    insights = [
        {
            "title": insight.title,
            "description": insight.description,
            "related_kpi": insight.related_kpi,
            "severity": insight.severity,
            "month": insight.month,
        }
        for insight in analysis.insights
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest agents/dashboard_agent/tests/test_layout_builder.py -v`
Expected: all PASS

- [ ] **Step 5: Run the full dashboard_agent suite**

Run: `python -m pytest agents/dashboard_agent/tests -q`
Expected: all PASS (no other test asserts exact-equality on the insights list)

- [ ] **Step 6: Commit**

```bash
git add agents/dashboard_agent/layout_builder.py agents/dashboard_agent/tests/test_layout_builder.py
git commit -m "Pass Insight.month through to the dashboard layout JSON"
```

---

## Task 3: `row_filters.py` — one filter definition per KPI

**Files:**
- Create: `agents/kpi_semantic_agent/row_filters.py`
- Test: `agents/kpi_semantic_agent/tests/test_row_filters.py`

**Interfaces:**
- Produces: `filter_rows(df: pd.DataFrame, business_domain: str, kpi_name: str, month: str | None = None) -> pd.DataFrame`, raising `KeyError` for an unknown `business_domain` or `kpi_name` (mirrors `compute_kpis`' own `raise KeyError(business_domain)`).
- Produces: `DATE_COLUMN_BY_DOMAIN: dict[str, str | None]` — reused by Task 4 for nothing extra (kept local to this module); documented here for Task 6's reference.

- [ ] **Step 1: Write the failing tests**

Create `agents/kpi_semantic_agent/tests/test_row_filters.py`:

```python
"""Tests for row_filters.py: the row-level filter behind each KPI."""

import pandas as pd
import pytest

from agents.kpi_semantic_agent.row_filters import filter_rows


def _ecommerce_df():
    return pd.DataFrame(
        {
            "order_id": ["o1", "o2", "o3"],
            "order_status": ["delivered", "delivered", "canceled"],
            "price": [100.0, 50.0, 999.0],
            "review_score": [5, None, 4],
            "order_purchase_timestamp": pd.to_datetime(
                ["2018-01-05", "2018-02-05", "2018-02-10"]
            ),
            "order_delivered_customer_date": pd.to_datetime(
                ["2018-01-10", None, "2018-02-15"]
            ),
            "order_estimated_delivery_date": pd.to_datetime(
                ["2018-01-12", "2018-02-08", "2018-02-12"]
            ),
        }
    )


def test_filter_rows_ecommerce_total_revenue_excludes_canceled():
    result = filter_rows(_ecommerce_df(), "e-commerce", "total_revenue")
    assert list(result["order_id"]) == ["o1", "o2"]


def test_filter_rows_ecommerce_order_count_has_no_filter():
    result = filter_rows(_ecommerce_df(), "e-commerce", "order_count")
    assert len(result) == 3


def test_filter_rows_ecommerce_average_review_score_drops_missing_reviews():
    result = filter_rows(_ecommerce_df(), "e-commerce", "average_review_score")
    assert list(result["order_id"]) == ["o1", "o3"]


def test_filter_rows_ecommerce_on_time_delivery_rate_keeps_delivered_only():
    result = filter_rows(_ecommerce_df(), "e-commerce", "on_time_delivery_rate")
    assert list(result["order_id"]) == ["o1", "o3"]


def test_filter_rows_ecommerce_scopes_to_a_month():
    result = filter_rows(_ecommerce_df(), "e-commerce", "order_count", month="2018-02")
    assert list(result["order_id"]) == ["o2", "o3"]


def test_filter_rows_unknown_kpi_raises_keyerror():
    with pytest.raises(KeyError):
        filter_rows(_ecommerce_df(), "e-commerce", "not_a_real_kpi")


def test_filter_rows_unknown_domain_raises_keyerror():
    with pytest.raises(KeyError):
        filter_rows(_ecommerce_df(), "not_a_real_domain", "total_revenue")


def _banking_df():
    return pd.DataFrame(
        {
            "trans_id": [1, 2, 3, 4],
            "type": ["PRIJEM", "PRIJEM", "VYDAJ", "VYDAJ"],
            "amount": [500.0, 300.0, 100.0, 50.0],
            "balance": [1000.0, None, 1200.0, 1150.0],
            "loan_status": ["C", "C", None, "C"],
            "date": pd.to_datetime(["2018-01-05", "2018-02-05", "2018-02-06", "2018-02-07"]),
        }
    )


def test_filter_rows_banking_total_transaction_volume_keeps_credits_only():
    result = filter_rows(_banking_df(), "banking", "total_transaction_volume")
    assert list(result["trans_id"]) == [1, 2]


def test_filter_rows_banking_average_account_balance_drops_missing_balance():
    result = filter_rows(_banking_df(), "banking", "average_account_balance")
    assert list(result["trans_id"]) == [1, 3, 4]


def test_filter_rows_banking_loan_good_standing_rate_keeps_rows_with_a_loan():
    result = filter_rows(_banking_df(), "banking", "loan_good_standing_rate")
    assert list(result["trans_id"]) == [1, 2, 4]


def test_filter_rows_banking_scopes_to_a_month():
    result = filter_rows(_banking_df(), "banking", "transaction_count", month="2018-02")
    assert list(result["trans_id"]) == [2, 3, 4]


def _telco_df():
    return pd.DataFrame(
        {
            "customer_id": ["c1", "c2"],
            "churn": ["Yes", "No"],
            "monthly_charges": [29.85, 56.95],
            "tenure": [1, 34],
        }
    )


def test_filter_rows_telco_kpis_have_no_filter():
    for kpi_name in (
        "churn_rate",
        "average_monthly_charges",
        "average_tenure_months",
        "total_customers",
    ):
        result = filter_rows(_telco_df(), "telco", kpi_name)
        assert len(result) == 2


def test_filter_rows_telco_ignores_month_since_there_is_no_date_column():
    result = filter_rows(_telco_df(), "telco", "total_customers", month="2018-02")
    assert len(result) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest agents/kpi_semantic_agent/tests/test_row_filters.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'agents.kpi_semantic_agent.row_filters'`

- [ ] **Step 3: Create `row_filters.py`**

Create `agents/kpi_semantic_agent/row_filters.py`:

```python
"""Row-level filters behind each KPI's value.

kpi_computation.py's aggregate functions and the dashboard API's
/api/drilldown endpoint both need "which rows count for this KPI" -- this
module is the single definition of that, so the two can't silently drift
apart if a KPI's filter ever changes.
"""

from typing import Callable

import pandas as pd

_RowFilter = Callable[[pd.DataFrame], pd.DataFrame]

_ECOMMERCE_FILTERS: dict[str, _RowFilter] = {
    "total_revenue": lambda df: df[df["order_status"] != "canceled"],
    "average_order_value": lambda df: df[df["order_status"] != "canceled"],
    "order_count": lambda df: df,
    "average_review_score": lambda df: df[df["review_score"].notna()],
    "on_time_delivery_rate": lambda df: df[df["order_delivered_customer_date"].notna()],
}

_BANKING_FILTERS: dict[str, _RowFilter] = {
    "total_transaction_volume": lambda df: df[df["type"] == "PRIJEM"],
    "average_transaction_value": lambda df: df[df["type"] == "PRIJEM"],
    "transaction_count": lambda df: df,
    "average_account_balance": lambda df: df[df["balance"].notna()],
    "loan_good_standing_rate": lambda df: df[df["loan_status"].notna()],
}

_TELCO_FILTERS: dict[str, _RowFilter] = {
    "churn_rate": lambda df: df,
    "average_monthly_charges": lambda df: df,
    "average_tenure_months": lambda df: df,
    "total_customers": lambda df: df,
}

_FILTERS_BY_DOMAIN: dict[str, dict[str, _RowFilter]] = {
    "e-commerce": _ECOMMERCE_FILTERS,
    "banking": _BANKING_FILTERS,
    "telco": _TELCO_FILTERS,
}

# The date column each domain's monthly trends bucket by (see
# bi_analyst_agent/monthly_trends.py), for month-scoped drill-downs. None
# where the domain has no time dimension (telco).
DATE_COLUMN_BY_DOMAIN: dict[str, str | None] = {
    "e-commerce": "order_purchase_timestamp",
    "banking": "date",
    "telco": None,
}


# Returns the analytical-table rows behind a KPI's value, optionally scoped to one month.
def filter_rows(
    df: pd.DataFrame, business_domain: str, kpi_name: str, month: str | None = None
) -> pd.DataFrame:
    """Returns the rows that back `kpi_name`'s value for `business_domain`.

    Raises KeyError for an unknown business_domain or kpi_name.
    """
    matching = _FILTERS_BY_DOMAIN[business_domain][kpi_name](df)

    date_column = DATE_COLUMN_BY_DOMAIN[business_domain]
    if month and date_column:
        dates = pd.to_datetime(matching[date_column])
        matching = matching[dates.dt.strftime("%Y-%m") == month]

    return matching
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest agents/kpi_semantic_agent/tests/test_row_filters.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add agents/kpi_semantic_agent/row_filters.py agents/kpi_semantic_agent/tests/test_row_filters.py
git commit -m "Add row_filters.py: one row-level filter definition per KPI"
```

---

## Task 4: Refactor `kpi_computation.py` to call `filter_rows`

**Files:**
- Modify: `agents/kpi_semantic_agent/kpi_computation.py:39-96` (`_compute_ecommerce_kpis`, `_compute_banking_kpis`)
- Test: `agents/kpi_semantic_agent/tests/test_kpi_computation.py` (existing — must keep passing unchanged, proving the refactor doesn't change any computed value)

**Interfaces:**
- Consumes: `filter_rows` from Task 3.

`_compute_telco_kpis` is intentionally left unchanged: none of its four
KPIs inline a filter condition today (each already just uses `df`
directly), so there's nothing to extract.

- [ ] **Step 1: Confirm the existing tests currently pass (baseline before refactor)**

Run: `python -m pytest agents/kpi_semantic_agent/tests/test_kpi_computation.py -v`
Expected: all PASS (this is the baseline — Step 3 must not change this)

- [ ] **Step 2: Add the import**

In `agents/kpi_semantic_agent/kpi_computation.py`, add after the existing imports:

```python
from agents.kpi_semantic_agent.row_filters import filter_rows
```

- [ ] **Step 3: Refactor `_compute_ecommerce_kpis`**

Change:

```python
def _compute_ecommerce_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the e-commerce KPI values from the order-item-level analytical table."""
    non_canceled = df[df["order_status"] != "canceled"]
    total_revenue = float(non_canceled["price"].sum())
    order_count = int(df["order_id"].nunique())
    non_canceled_order_count = int(non_canceled["order_id"].nunique())
    average_order_value = (
        total_revenue / non_canceled_order_count if non_canceled_order_count else 0.0
    )

    average_review_score = float(df["review_score"].mean())

    delivered = df[df["order_delivered_customer_date"].notna()]
    on_time_delivery_rate = (
        float(
            (
                delivered["order_delivered_customer_date"]
                <= delivered["order_estimated_delivery_date"]
            ).mean()
        )
        if len(delivered)
        else None
    )
```

to:

```python
def _compute_ecommerce_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the e-commerce KPI values from the order-item-level analytical table."""
    non_canceled = filter_rows(df, "e-commerce", "total_revenue")
    total_revenue = float(non_canceled["price"].sum())
    order_count = int(df["order_id"].nunique())
    non_canceled_order_count = int(non_canceled["order_id"].nunique())
    average_order_value = (
        total_revenue / non_canceled_order_count if non_canceled_order_count else 0.0
    )

    reviewed = filter_rows(df, "e-commerce", "average_review_score")
    average_review_score = float(reviewed["review_score"].mean())

    delivered = filter_rows(df, "e-commerce", "on_time_delivery_rate")
    on_time_delivery_rate = (
        float(
            (
                delivered["order_delivered_customer_date"]
                <= delivered["order_estimated_delivery_date"]
            ).mean()
        )
        if len(delivered)
        else None
    )
```

(The rest of the function, including the final `return` dict, is unchanged.)

- [ ] **Step 4: Refactor `_compute_banking_kpis`**

Change:

```python
def _compute_banking_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the banking KPI values from the transaction-level analytical table."""
    credits = df[df["type"] == "PRIJEM"]
    total_transaction_volume = float(credits["amount"].sum())
    transaction_count = int(df["trans_id"].nunique())
    credit_transaction_count = int(credits["trans_id"].nunique())
    average_transaction_value = (
        total_transaction_volume / credit_transaction_count if credit_transaction_count else 0.0
    )

    average_account_balance = float(df["balance"].mean())

    with_loan = df[df["loan_status"].notna()]
    loan_good_standing_rate = (
        float(with_loan["loan_status"].isin(["A", "C"]).mean()) if len(with_loan) else None
    )
```

to:

```python
def _compute_banking_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Computes the banking KPI values from the transaction-level analytical table."""
    credits = filter_rows(df, "banking", "total_transaction_volume")
    total_transaction_volume = float(credits["amount"].sum())
    transaction_count = int(df["trans_id"].nunique())
    credit_transaction_count = int(credits["trans_id"].nunique())
    average_transaction_value = (
        total_transaction_volume / credit_transaction_count if credit_transaction_count else 0.0
    )

    balance_rows = filter_rows(df, "banking", "average_account_balance")
    average_account_balance = float(balance_rows["balance"].mean())

    with_loan = filter_rows(df, "banking", "loan_good_standing_rate")
    loan_good_standing_rate = (
        float(with_loan["loan_status"].isin(["A", "C"]).mean()) if len(with_loan) else None
    )
```

(The rest of the function, including the final `return` dict, is unchanged.)

- [ ] **Step 5: Run tests to verify nothing changed**

Run: `python -m pytest agents/kpi_semantic_agent/tests/test_kpi_computation.py -v`
Expected: all PASS, identical to Step 1's baseline

- [ ] **Step 6: Run the full kpi_semantic_agent suite and the end-to-end pipeline test**

Run: `python -m pytest agents/kpi_semantic_agent/tests tests/test_end_to_end.py -q`
Expected: all PASS — confirms the refactor doesn't change any KPI value across the real sample datasets

- [ ] **Step 7: Commit**

```bash
git add agents/kpi_semantic_agent/kpi_computation.py
git commit -m "Refactor kpi_computation.py to reuse row_filters.filter_rows"
```

---

## Task 5: Domain-scope the analytical table path in the live pipeline endpoint

**Files:**
- Modify: `agents/dashboard_agent/api.py:1-113`
- Test: `agents/dashboard_agent/tests/test_api.py:28-53,238-251`

**Interfaces:**
- Consumes: `DEFAULT_OUTPUT_PATH` from `agents/data_engineering_agent/agent.py`.
- Produces: `_analytical_path_for(domain: str | None) -> str` (closure inside `create_app`, mirrors `_layout_path_for`) — consumed by Task 6.

This is a prerequisite bug fix: today, `run_pipeline` domain-scopes the
dashboard layout path but not the analytical table path, so two domains
run back-to-back overwrite the same `data/processed/analytical_table.csv`.
Task 6's drill-down endpoint reads that file, so it must be domain-scoped
first or drill-down could silently show the wrong domain's rows.

- [ ] **Step 1: Write the failing test**

The existing fakes in `agents/dashboard_agent/tests/test_api.py` only
accept `dashboard_layout_path` and `on_event` — add `analytical_path` to
both, and a spy to prove it's domain-scoped. Change:

```python
class _FakeOrchestrator:
    """Stands in for BIFlowOrchestrator: emits events without touching real data."""

    STAGES = ["data_engineering", "kpi_semantic", "bi_analyst", "dashboard", "auditor"]

    def __init__(self, dashboard_layout_path, on_event):
        self.on_event = on_event

    def run_pipeline(self, raw_dataset):
        for stage in self.STAGES:
            self.on_event(stage, "started", {})
            self.on_event(stage, "succeeded", {})


class _FailingFakeOrchestrator:
    """Fails partway through, like a real stage raising an exception."""

    def __init__(self, dashboard_layout_path, on_event):
        self.on_event = on_event

    def run_pipeline(self, raw_dataset):
        self.on_event("data_engineering", "started", {})
        self.on_event("data_engineering", "succeeded", {})
        self.on_event("kpi_semantic", "started", {})
        self.on_event("kpi_semantic", "failed", {"error": "boom"})
        raise PipelineStageError("kpi_semantic", ValueError("boom"))
```

to:

```python
class _FakeOrchestrator:
    """Stands in for BIFlowOrchestrator: emits events without touching real data."""

    STAGES = ["data_engineering", "kpi_semantic", "bi_analyst", "dashboard", "auditor"]
    last_analytical_path = None

    def __init__(self, analytical_path, dashboard_layout_path, on_event):
        _FakeOrchestrator.last_analytical_path = analytical_path
        self.on_event = on_event

    def run_pipeline(self, raw_dataset):
        for stage in self.STAGES:
            self.on_event(stage, "started", {})
            self.on_event(stage, "succeeded", {})


class _FailingFakeOrchestrator:
    """Fails partway through, like a real stage raising an exception."""

    def __init__(self, analytical_path, dashboard_layout_path, on_event):
        self.on_event = on_event

    def run_pipeline(self, raw_dataset):
        self.on_event("data_engineering", "started", {})
        self.on_event("data_engineering", "succeeded", {})
        self.on_event("kpi_semantic", "started", {})
        self.on_event("kpi_semantic", "failed", {"error": "boom"})
        raise PipelineStageError("kpi_semantic", ValueError("boom"))
```

Then add a new test, after `test_run_pipeline_streams_a_stage_event_per_transition`:

```python
def test_run_pipeline_scopes_the_analytical_path_to_the_domain(tmp_path, monkeypatch):
    monkeypatch.setattr("agents.dashboard_agent.api.BIFlowOrchestrator", _FakeOrchestrator)
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    client.get("/api/pipeline/run", params={"domain": "banking"})

    assert _FakeOrchestrator.last_analytical_path.endswith("analytical_table_banking.csv")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest agents/dashboard_agent/tests/test_api.py -k run_pipeline -v`
Expected: `test_run_pipeline_streams_a_stage_event_per_transition` and
`test_run_pipeline_streams_failure_and_stops` FAIL with
`TypeError: _FakeOrchestrator.__init__() missing 1 required positional argument: 'analytical_path'`
(the fakes now require it, but `api.py` doesn't pass it yet); the new
scoping test FAILs the same way.

- [ ] **Step 3: Add `_analytical_path_for` and pass it through**

In `agents/dashboard_agent/api.py`, add the import:

```python
from agents.data_engineering_agent.agent import DEFAULT_OUTPUT_PATH
```

Inside `create_app`, after `resolved_layout_path` is computed, add:

```python
    resolved_analytical_path = os.environ.get("ANALYTICAL_TABLE_PATH", DEFAULT_OUTPUT_PATH)
```

After the existing `_layout_path_for` closure, add a sibling closure:

```python
    # Resolves which analytical table CSV to read: a domain-specific one
    # (written by a live-triggered run for that domain, e.g.
    # analytical_table_banking.csv) when a domain is given, otherwise the
    # path a domain-less CLI run writes to. Mirrors _layout_path_for.
    def _analytical_path_for(domain: str | None) -> str:
        if not domain:
            return resolved_analytical_path
        if domain not in ALLOWED_DOMAINS:
            raise HTTPException(status_code=404, detail=f"Unknown domain: {domain!r}")
        directory = os.path.dirname(resolved_analytical_path) or "."
        base, ext = os.path.splitext(os.path.basename(resolved_analytical_path))
        return os.path.join(directory, f"{base}_{domain}{ext}")
```

In `run_pipeline`, change:

```python
    def run_pipeline(domain: str) -> StreamingResponse:
        layout_path = _layout_path_for(domain)  # validates domain against ALLOWED_DOMAINS
        dataset_path, dataset_name = DOMAIN_DATASETS[domain]
```

to:

```python
    def run_pipeline(domain: str) -> StreamingResponse:
        layout_path = _layout_path_for(domain)  # validates domain against ALLOWED_DOMAINS
        analytical_path = _analytical_path_for(domain)
        dataset_path, dataset_name = DOMAIN_DATASETS[domain]
```

and change:

```python
        def run() -> None:
            pipeline = BIFlowOrchestrator(dashboard_layout_path=layout_path, on_event=on_event)
```

to:

```python
        def run() -> None:
            pipeline = BIFlowOrchestrator(
                analytical_path=analytical_path,
                dashboard_layout_path=layout_path,
                on_event=on_event,
            )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest agents/dashboard_agent/tests/test_api.py -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add agents/dashboard_agent/api.py agents/dashboard_agent/tests/test_api.py
git commit -m "Domain-scope the analytical table path for live-triggered pipeline runs"
```

---

## Task 6: `GET /api/drilldown` endpoint

**Files:**
- Modify: `agents/dashboard_agent/api.py`
- Test: `agents/dashboard_agent/tests/test_api.py`

**Interfaces:**
- Consumes: `filter_rows` (Task 3), `_analytical_path_for` (Task 5).
- Produces: `GET /api/drilldown?domain=&kpi=&month=` → `{"total_rows": int, "columns": list[str], "rows": list[dict]}`, 404 for an unknown domain/kpi or a missing analytical file.

- [ ] **Step 1: Write the failing tests**

Add to `agents/dashboard_agent/tests/test_api.py`:

```python
def _write_analytical_csv(tmp_path, domain, rows_csv):
    path = tmp_path / f"analytical_table_{domain}.csv"
    path.write_text(rows_csv)
    return str(path)


def _client_with_analytical_dir(tmp_path, monkeypatch):
    # _analytical_path_for derives its directory from ANALYTICAL_TABLE_PATH
    # (defaulting to data/processed/analytical_table.csv otherwise), same as
    # _layout_path_for derives it from the layout_path passed to create_app.
    monkeypatch.setenv("ANALYTICAL_TABLE_PATH", str(tmp_path / "analytical_table.csv"))
    return TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))


def test_drilldown_endpoint_returns_matching_rows(tmp_path, monkeypatch):
    _write_analytical_csv(
        tmp_path,
        "e-commerce",
        "order_id,order_status,price\no1,delivered,100.0\no2,canceled,999.0\n",
    )
    client = _client_with_analytical_dir(tmp_path, monkeypatch)

    response = client.get(
        "/api/drilldown", params={"domain": "e-commerce", "kpi": "total_revenue"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 1
    assert body["columns"] == ["order_id", "order_status", "price"]
    assert body["rows"] == [{"order_id": "o1", "order_status": "delivered", "price": 100.0}]


def test_drilldown_endpoint_scopes_to_a_month(tmp_path, monkeypatch):
    _write_analytical_csv(
        tmp_path,
        "banking",
        "trans_id,type,amount,date\n"
        "1,PRIJEM,100.0,2018-01-05\n"
        "2,PRIJEM,200.0,2018-02-05\n",
    )
    client = _client_with_analytical_dir(tmp_path, monkeypatch)

    response = client.get(
        "/api/drilldown",
        params={"domain": "banking", "kpi": "total_transaction_volume", "month": "2018-02"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_rows"] == 1
    assert body["rows"][0]["trans_id"] == 2


def test_drilldown_endpoint_returns_404_for_unknown_domain(tmp_path, monkeypatch):
    client = _client_with_analytical_dir(tmp_path, monkeypatch)

    response = client.get(
        "/api/drilldown", params={"domain": "unknown", "kpi": "total_revenue"}
    )

    assert response.status_code == 404


def test_drilldown_endpoint_returns_404_for_unknown_kpi(tmp_path, monkeypatch):
    _write_analytical_csv(tmp_path, "e-commerce", "order_id,price\no1,100.0\n")
    client = _client_with_analytical_dir(tmp_path, monkeypatch)

    response = client.get(
        "/api/drilldown", params={"domain": "e-commerce", "kpi": "not_a_real_kpi"}
    )

    assert response.status_code == 404


def test_drilldown_endpoint_returns_404_when_no_analytical_table_exists(tmp_path, monkeypatch):
    client = _client_with_analytical_dir(tmp_path, monkeypatch)

    response = client.get(
        "/api/drilldown", params={"domain": "telco", "kpi": "total_customers"}
    )

    assert response.status_code == 404


def test_drilldown_endpoint_caps_rows_at_fifty(tmp_path, monkeypatch):
    header = "order_id,order_status,price\n"
    body_rows = "\n".join(f"o{i},delivered,10.0" for i in range(60))
    _write_analytical_csv(tmp_path, "e-commerce", header + body_rows + "\n")
    client = _client_with_analytical_dir(tmp_path, monkeypatch)

    response = client.get(
        "/api/drilldown", params={"domain": "e-commerce", "kpi": "order_count"}
    )

    body = response.json()
    assert body["total_rows"] == 60
    assert len(body["rows"]) == 50
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest agents/dashboard_agent/tests/test_api.py -k drilldown -v`
Expected: FAIL — `404 Not Found` for the app (no `/api/drilldown` route registered yet)

- [ ] **Step 3: Add the endpoint**

In `agents/dashboard_agent/api.py`, add imports:

```python
import pandas as pd

from agents.kpi_semantic_agent.row_filters import filter_rows
```

Inside `create_app`, after the `_analytical_path_for` closure from Task 5,
add:

```python
    _analytical_df_cache: dict[str, tuple[float, pd.DataFrame]] = {}

    # Loads an analytical CSV into memory, cached by (path, mtime) so repeat
    # drill-down requests don't re-read a potentially million-row file.
    def _load_analytical_df(path: str) -> pd.DataFrame:
        mtime = os.path.getmtime(path)
        cached = _analytical_df_cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
        df = pd.read_csv(path, low_memory=False)
        _analytical_df_cache[path] = (mtime, df)
        return df
```

After the `/api/dashboard` route, add:

```python
    DRILLDOWN_ROW_LIMIT = 50

    # Serves the raw analytical-table rows behind one KPI's value, optionally scoped to a month.
    @app.get("/api/drilldown")
    def drilldown(domain: str, kpi: str, month: str | None = None) -> dict:
        path = _analytical_path_for(domain)  # validates domain against ALLOWED_DOMAINS
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="No dashboard data yet — run the pipeline first.")
        df = _load_analytical_df(path)
        try:
            matching = filter_rows(df, domain, kpi, month)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown KPI: {kpi!r}")
        page = matching.head(DRILLDOWN_ROW_LIMIT)
        return {
            "total_rows": int(len(matching)),
            "columns": list(page.columns),
            "rows": json.loads(page.to_json(orient="records")),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest agents/dashboard_agent/tests/test_api.py -v`
Expected: all PASS

- [ ] **Step 5: Run the full dashboard_agent suite**

Run: `python -m pytest agents/dashboard_agent/tests -q`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add agents/dashboard_agent/api.py agents/dashboard_agent/tests/test_api.py
git commit -m "Add GET /api/drilldown endpoint"
```

---

## Task 7: Frontend types

**Files:**
- Modify: `frontend/src/app/dashboard/types.ts`

**Interfaces:**
- Produces: `Insight.month?: string | null`, `DrillDownResponse` type — consumed by Task 8, 9, 10.

- [ ] **Step 1: Update `types.ts`**

In `frontend/src/app/dashboard/types.ts`, change:

```typescript
export interface Insight {
  title: string;
  description: string;
  related_kpi: string;
  severity: "info" | "warning" | "critical" | string;
}
```

to:

```typescript
export interface Insight {
  title: string;
  description: string;
  related_kpi: string;
  severity: "info" | "warning" | "critical" | string;
  month?: string | null;
}
```

Add at the end of the file:

```typescript
export interface DrillDownResponse {
  total_rows: number;
  columns: string[];
  rows: Record<string, unknown>[];
}
```

- [ ] **Step 2: Run the frontend build/typecheck to confirm nothing else broke**

Run: `cd frontend && npx tsc --noEmit`
Expected: no new type errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/dashboard/types.ts
git commit -m "Add Insight.month and DrillDownResponse types"
```

---

## Task 8: `DrillDownPanel.tsx` component

**Files:**
- Create: `frontend/src/app/dashboard/DrillDownPanel.tsx`
- Modify: `frontend/src/app/dashboard/page.module.css` (append new classes)
- Test: `frontend/src/app/dashboard/DrillDownPanel.test.tsx`

**Interfaces:**
- Consumes: `DrillDownResponse` (Task 7).
- Produces: `DrillDownPanel({ domain: string; kpiName: string; month?: string | null; formula?: string | null })` — a React component, default export. Consumed by Task 9 and Task 10.

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/app/dashboard/DrillDownPanel.test.tsx`:

```typescript
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import DrillDownPanel from "./DrillDownPanel";

function mockFetchOnce(response: Partial<Response> & { jsonBody?: unknown }) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: response.ok ?? true,
    status: response.status ?? 200,
    json: async () => response.jsonBody,
  } as Response);
}

afterEach(() => {
  jest.restoreAllMocks();
});

describe("DrillDownPanel", () => {
  it("starts collapsed and does not fetch until toggled", () => {
    global.fetch = jest.fn();
    render(<DrillDownPanel domain="e-commerce" kpiName="total_revenue" />);

    expect(screen.getByText(/view underlying rows/i)).toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("fetches and renders rows when toggled open", async () => {
    mockFetchOnce({
      jsonBody: {
        total_rows: 1,
        columns: ["order_id", "price"],
        rows: [{ order_id: "o1", price: 100 }],
      },
    });

    render(<DrillDownPanel domain="e-commerce" kpiName="total_revenue" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));

    expect(await screen.findByText("o1")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText(/1 row matched/i)).toBeInTheDocument();

    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("domain=e-commerce");
    expect(url).toContain("kpi=total_revenue");
  });

  it("includes the month in the request when given", async () => {
    mockFetchOnce({ jsonBody: { total_rows: 0, columns: [], rows: [] } });

    render(
      <DrillDownPanel domain="banking" kpiName="total_transaction_volume" month="2018-02" />
    );
    fireEvent.click(screen.getByText(/view underlying rows/i));

    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("month=2018-02");
  });

  it("shows a note when the row cap is hit", async () => {
    mockFetchOnce({
      jsonBody: {
        total_rows: 60,
        columns: ["order_id"],
        rows: Array.from({ length: 50 }, (_, i) => ({ order_id: `o${i}` })),
      },
    });

    render(<DrillDownPanel domain="e-commerce" kpiName="order_count" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));

    expect(await screen.findByText(/showing first 50/i)).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    mockFetchOnce({ ok: false, status: 404, jsonBody: { detail: "Unknown KPI: 'x'" } });

    render(<DrillDownPanel domain="e-commerce" kpiName="x" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));

    expect(await screen.findByText("Unknown KPI: 'x'")).toBeInTheDocument();
  });

  it("collapses again when toggled a second time", async () => {
    mockFetchOnce({
      jsonBody: { total_rows: 1, columns: ["order_id"], rows: [{ order_id: "o1" }] },
    });

    render(<DrillDownPanel domain="e-commerce" kpiName="total_revenue" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));
    await screen.findByText("o1");

    fireEvent.click(screen.getByText(/hide underlying rows/i));
    expect(screen.queryByText("o1")).not.toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx jest DrillDownPanel.test.tsx`
Expected: FAIL — cannot find module `./DrillDownPanel`

- [ ] **Step 3: Create `DrillDownPanel.tsx`**

Create `frontend/src/app/dashboard/DrillDownPanel.tsx`:

```typescript
"use client";

import { useState } from "react";
import styles from "./page.module.css";
import type { DrillDownResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type DrillDownState =
  | { status: "collapsed" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DrillDownResponse };

// Fetches the rows behind a KPI (optionally scoped to one month) from /api/drilldown.
async function fetchDrillDown(
  domain: string,
  kpiName: string,
  month?: string | null
): Promise<DrillDownState> {
  try {
    const params = new URLSearchParams({ domain, kpi: kpiName });
    if (month) params.set("month", month);
    const response = await fetch(`${API_URL}/api/drilldown?${params}`, { cache: "no-store" });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as { detail?: string } | null;
      return { status: "error", message: body?.detail ?? `API returned ${response.status}` };
    }
    const data = (await response.json()) as DrillDownResponse;
    return { status: "ready", data };
  } catch {
    return { status: "error", message: "Could not reach the dashboard API." };
  }
}

// Collapsed-by-default panel: on expand, fetches and shows the raw rows behind a KPI's value.
export default function DrillDownPanel({
  domain,
  kpiName,
  month,
  formula,
}: {
  domain: string;
  kpiName: string;
  month?: string | null;
  formula?: string | null;
}) {
  const [state, setState] = useState<DrillDownState>({ status: "collapsed" });

  const handleToggle = () => {
    if (state.status === "collapsed") {
      setState({ status: "loading" });
      fetchDrillDown(domain, kpiName, month).then(setState);
    } else {
      setState({ status: "collapsed" });
    }
  };

  return (
    <div className={styles.drillDown}>
      <button type="button" className={styles.drillToggle} onClick={handleToggle}>
        {state.status === "collapsed" ? "View underlying rows ▸" : "Hide underlying rows ▾"}
      </button>

      {state.status === "loading" && <p className={styles.noTrend}>Loading…</p>}
      {state.status === "error" && <p className={styles.error}>{state.message}</p>}

      {state.status === "ready" && (
        <div className={styles.drillPanel}>
          <p className={styles.drillSummary}>
            {formula && <span>{formula}</span>}
            {month && <span> · {month}</span>}
            {(formula || month) && " · "}
            {state.data.total_rows} row{state.data.total_rows === 1 ? "" : "s"} matched
            {state.data.total_rows > state.data.rows.length &&
              ` (showing first ${state.data.rows.length})`}
          </p>
          {state.data.rows.length > 0 ? (
            <div className={styles.drillTableWrap}>
              <table className={styles.drillTable}>
                <thead>
                  <tr>
                    {state.data.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {state.data.rows.map((row, i) => (
                    <tr key={i}>
                      {state.data.columns.map((col) => (
                        <td key={col}>{String(row[col] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className={styles.noTrend}>No rows matched.</p>
          )}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Append the new CSS classes**

Append to the end of `frontend/src/app/dashboard/page.module.css`:

```css
.drillDown {
  margin-top: 0.75rem;
}

.drillToggle {
  font-family: var(--font-plex-mono), ui-monospace, monospace;
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--accent);
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.drillPanel {
  margin-top: 0.6rem;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem;
  background: var(--surface);
}

.drillSummary {
  font-family: var(--font-plex-mono), ui-monospace, monospace;
  font-size: 0.72rem;
  color: var(--foreground-muted);
  margin: 0 0 0.6rem;
}

.drillTableWrap {
  overflow-x: auto;
  overflow-y: auto;
  max-height: 320px;
}

.drillTable {
  border-collapse: collapse;
  font-size: 0.75rem;
  white-space: nowrap;
}

.drillTable th,
.drillTable td {
  padding: 0.35rem 0.6rem;
  border-bottom: 1px solid var(--border);
  text-align: left;
}

.drillTable th {
  font-family: var(--font-plex-mono), ui-monospace, monospace;
  font-weight: 600;
  color: var(--foreground-muted);
  position: sticky;
  top: 0;
  background: var(--surface);
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd frontend && npx jest DrillDownPanel.test.tsx`
Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add frontend/src/app/dashboard/DrillDownPanel.tsx frontend/src/app/dashboard/DrillDownPanel.test.tsx frontend/src/app/dashboard/page.module.css
git commit -m "Add DrillDownPanel component"
```

---

## Task 9: Wire `DrillDownPanel` into the KPI-card detail view

**Files:**
- Modify: `frontend/src/app/dashboard/KpiDetail.tsx`
- Modify: `frontend/src/app/dashboard/page.tsx:245-254` (the `KpiDetail` call site)
- Modify: `frontend/src/app/dashboard/page.module.css` (the `.insight`/`.insight + .insight` rules)
- Test: `frontend/src/app/dashboard/page.test.tsx`

**Interfaces:**
- Consumes: `DrillDownPanel` (Task 8).
- Produces: `KpiDetail` gains a required `domain: string | null` prop.

This task also splits `.insight`'s CSS: the "border between adjacent
insights" rule moves from `.insight + .insight` (which assumed `.insight`
was always the direct `<li>`) to a new `.insightRow` class on the `<li>`,
because Task 10 needs the `<li>`'s content to sometimes be a `<button>`
and sometimes hold an expanded panel below it. This task updates
`KpiDetail.tsx`'s own (non-interactive) related-insights list to the new
markup shape so both files stay consistent; Task 10 does the same for the
main Insights tab.

- [ ] **Step 1: Write the failing test**

Add to `frontend/src/app/dashboard/page.test.tsx`, after the existing
`"shows a KPI's explanation and related insights when its card is clicked"`
test:

```typescript
  it("shows a drill-down toggle in the KPI detail panel when a domain is set", async () => {
    mockSearchParams.get.mockReturnValue("e-commerce");
    const layout: DashboardLayout = {
      kpi_cards: [
        {
          name: "total_revenue",
          label: "Total revenue",
          value: 123.45,
          explanation: "total_revenue = sum(price) = 123.45",
        },
      ],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    fireEvent.click(await screen.findByText("Total revenue"));

    const detail = within(await screen.findByTestId("kpi-detail"));
    expect(detail.getByText(/view underlying rows/i)).toBeInTheDocument();
  });

  it("does not show a drill-down toggle when no domain is set", async () => {
    mockSearchParams.get.mockReturnValue(null);
    const layout: DashboardLayout = {
      kpi_cards: [{ name: "total_revenue", label: "Total revenue", value: 123.45 }],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    fireEvent.click(await screen.findByText("Total revenue"));

    const detail = within(await screen.findByTestId("kpi-detail"));
    expect(detail.queryByText(/view underlying rows/i)).not.toBeInTheDocument();
  });
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx jest page.test.tsx -t "drill-down"`
Expected: FAIL — `KpiDetail` doesn't render a "View underlying rows" toggle yet (`domain` prop doesn't exist)

- [ ] **Step 3: Update `KpiDetail.tsx`**

Replace the full contents of `frontend/src/app/dashboard/KpiDetail.tsx`
with:

```typescript
"use client";

import DrillDownPanel from "./DrillDownPanel";
import styles from "./page.module.css";
import TrendChart from "./TrendChart";
import type { Insight, KpiCard, MonthlyTrendPoint } from "./types";

// Expanded panel for a selected KPI: shows its explanation, trend chart, drill-down rows, and related insights.
export default function KpiDetail({
  card,
  trendSeries,
  insights,
  domain,
  onClose,
}: {
  card: KpiCard;
  trendSeries: MonthlyTrendPoint[] | undefined;
  insights: Insight[];
  domain: string | null;
  onClose: () => void;
}) {
  return (
    <section className={styles.detailPanel} data-testid="kpi-detail">
      <div className={styles.detailHeader}>
        <h2 className={styles.subheading}>{card.label}</h2>
        <button
          type="button"
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Close KPI details"
        >
          ×
        </button>
      </div>

      {card.explanation && (
        <>
          <p className={styles.explanationLabel}>Formula</p>
          <p className={styles.explanation}>{card.explanation}</p>
        </>
      )}

      {trendSeries ? (
        <TrendChart metric={card.name} series={trendSeries} />
      ) : (
        <p className={styles.noTrend}>No trend data available for this KPI.</p>
      )}

      {domain && (
        <DrillDownPanel domain={domain} kpiName={card.name} formula={card.explanation} />
      )}

      {insights.length > 0 && (
        <ul className={styles.insightList}>
          {insights.map((insight, i) => (
            <li key={i} className={styles.insightRow}>
              <div
                className={`${styles.insight} ${styles[`severity-${insight.severity}`] ?? ""}`}
              >
                <span className={styles.insightText}>
                  <strong>{insight.title}</strong> — {insight.description}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
```

- [ ] **Step 4: Update the `KpiDetail` call site in `page.tsx`**

In `frontend/src/app/dashboard/page.tsx`, change:

```typescript
                      return (
                        <KpiDetail
                          card={selectedCard}
                          trendSeries={data.monthly_trends[selectedKpiName]}
                          insights={data.insights.filter(
                            (insight) => insight.related_kpi === selectedKpiName
                          )}
                          onClose={() => setSelectedKpiName(null)}
                        />
                      );
```

to:

```typescript
                      return (
                        <KpiDetail
                          card={selectedCard}
                          trendSeries={data.monthly_trends[selectedKpiName]}
                          insights={data.insights.filter(
                            (insight) => insight.related_kpi === selectedKpiName
                          )}
                          domain={domain}
                          onClose={() => setSelectedKpiName(null)}
                        />
                      );
```

- [ ] **Step 5: Update the `.insight` CSS**

In `frontend/src/app/dashboard/page.module.css`, change:

```css
.insight {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.85rem 1.1rem;
  background: var(--surface);
  font-size: 0.9rem;
}

.insight + .insight {
  border-top: 1px solid var(--border);
}
```

to:

```css
.insightRow {
  background: var(--surface);
}

.insightRow + .insightRow {
  border-top: 1px solid var(--border);
}

.insight {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  width: 100%;
  padding: 0.85rem 1.1rem;
  border: none;
  background: none;
  font-family: inherit;
  font-size: 0.9rem;
  color: inherit;
  text-align: left;
}

button.insight {
  cursor: pointer;
}
```

(`.insight::before` and the `.severity-*::before` rules below it are
unchanged — they still target the element carrying both `.insight` and
`.severity-<level>`, which is now the inner `<div>`/`<button>` instead of
the `<li>`.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd frontend && npx jest page.test.tsx`
Expected: all PASS, including the two new tests and every pre-existing
`page.test.tsx` test (they all run with `mockSearchParams.get` returning
`null` by default via `beforeEach`, so `KpiDetail` renders without the new
drill-down toggle in those — unaffected)

- [ ] **Step 7: Commit**

```bash
git add frontend/src/app/dashboard/KpiDetail.tsx frontend/src/app/dashboard/page.tsx frontend/src/app/dashboard/page.module.css frontend/src/app/dashboard/page.test.tsx
git commit -m "Wire DrillDownPanel into the KPI detail panel"
```

---

## Task 10: Make the Insights tab drillable

**Files:**
- Modify: `frontend/src/app/dashboard/page.tsx`
- Modify: `frontend/src/app/dashboard/page.module.css` (append `.insightDrillDown`)
- Test: `frontend/src/app/dashboard/page.test.tsx`

**Interfaces:**
- Consumes: `DrillDownPanel` (Task 8), `.insightRow`/`.insight` (Task 9).

- [ ] **Step 1: Write the failing tests**

Add to `frontend/src/app/dashboard/page.test.tsx`:

```typescript
  it("expands a drill-down panel when an insight is clicked", async () => {
    mockSearchParams.get.mockReturnValue("e-commerce");
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [
        {
          title: "Revenue up",
          description: "Grew 10%",
          related_kpi: "total_revenue",
          severity: "info",
          month: "2018-02",
        },
      ],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByRole("tab", { name: /overview/i });
    goToTab("Insights");
    fireEvent.click(screen.getByText("Revenue up", { exact: false }));

    expect(await screen.findByText(/view underlying rows/i)).toBeInTheDocument();
  });

  it("does not make an insight with no related KPI clickable", async () => {
    mockSearchParams.get.mockReturnValue("telco");
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [
        {
          title: "No month-over-month trends available",
          description: "The telco dataset has no transaction dates.",
          related_kpi: "",
          severity: "info",
        },
      ],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByRole("tab", { name: /overview/i });
    goToTab("Insights");

    expect(
      screen.queryByRole("button", { name: /no month-over-month trends available/i })
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("No month-over-month trends available", { exact: false })
    ).toBeInTheDocument();
  });
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd frontend && npx jest page.test.tsx -t "drill-down panel when an insight"`
Expected: FAIL — insights aren't clickable yet, no drill-down toggle appears

- [ ] **Step 3: Add `selectedInsightIndex` state**

In `frontend/src/app/dashboard/page.tsx`, change:

```typescript
  const [selectedKpiName, setSelectedKpiName] = useState<string | null>(null);
```

to:

```typescript
  const [selectedKpiName, setSelectedKpiName] = useState<string | null>(null);
  const [selectedInsightIndex, setSelectedInsightIndex] = useState<number | null>(null);
```

- [ ] **Step 4: Rewrite the Insights tab section**

In `frontend/src/app/dashboard/page.tsx`, change:

```typescript
                  {insights.length > 0 ? (
                    <ul className={styles.insightList}>
                      {insights.map((insight, i) => (
                        <li
                          key={i}
                          className={`${styles.insight} ${
                            styles[`severity-${insight.severity}`] ?? ""
                          }`}
                        >
                          <span className={styles.insightText}>
                            <strong>{insight.title}</strong> — {insight.description}
                          </span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className={styles.noTrend}>No insights generated for this run.</p>
                  )}
```

to:

```typescript
                  {insights.length > 0 ? (
                    <ul className={styles.insightList}>
                      {insights.map((insight, i) => {
                        const isDrillable = insight.related_kpi !== "";
                        const isSelected = selectedInsightIndex === i;
                        return (
                          <li key={i} className={styles.insightRow}>
                            {isDrillable ? (
                              <button
                                type="button"
                                className={`${styles.insight} ${
                                  styles[`severity-${insight.severity}`] ?? ""
                                }`}
                                aria-expanded={isSelected}
                                onClick={() =>
                                  setSelectedInsightIndex(isSelected ? null : i)
                                }
                              >
                                <span className={styles.insightText}>
                                  <strong>{insight.title}</strong> — {insight.description}
                                </span>
                              </button>
                            ) : (
                              <div
                                className={`${styles.insight} ${
                                  styles[`severity-${insight.severity}`] ?? ""
                                }`}
                              >
                                <span className={styles.insightText}>
                                  <strong>{insight.title}</strong> — {insight.description}
                                </span>
                              </div>
                            )}
                            {isDrillable && isSelected && domain && (
                              <div className={styles.insightDrillDown}>
                                <DrillDownPanel
                                  domain={domain}
                                  kpiName={insight.related_kpi}
                                  month={insight.month}
                                />
                              </div>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className={styles.noTrend}>No insights generated for this run.</p>
                  )}
```

- [ ] **Step 5: Add the `DrillDownPanel` import**

In `frontend/src/app/dashboard/page.tsx`, change:

```typescript
import CategoryChart from "./CategoryChart";
```

to:

```typescript
import CategoryChart from "./CategoryChart";
import DrillDownPanel from "./DrillDownPanel";
```

- [ ] **Step 6: Append the `.insightDrillDown` CSS class**

Append to `frontend/src/app/dashboard/page.module.css`:

```css
.insightDrillDown {
  padding: 0 1.1rem 0.85rem;
}
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd frontend && npx jest page.test.tsx`
Expected: all PASS

- [ ] **Step 8: Run the full frontend test suite**

Run: `cd frontend && npm test`
Expected: all PASS

- [ ] **Step 9: Commit**

```bash
git add frontend/src/app/dashboard/page.tsx frontend/src/app/dashboard/page.module.css frontend/src/app/dashboard/page.test.tsx
git commit -m "Make insights with a related KPI drillable"
```

---

## Final verification

- [ ] Run the full backend suite: `python -m pytest -q` — expect only the
      4 pre-existing Postgres-connectivity failures (no local Postgres
      running), everything else PASS.
- [ ] Run the full frontend suite: `cd frontend && npm test` — expect all
      PASS.
- [ ] Manually smoke-test: start `biflow-api` and `biflow-frontend`
      (`.claude/launch.json`), trigger a live pipeline run for one domain,
      open its dashboard, click a KPI card and a drillable insight, confirm
      the "View underlying rows" toggle fetches and renders a row table.

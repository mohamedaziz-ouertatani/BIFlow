# Auditor/XAI drill-down in the dashboard

**Date:** 2026-09-18
**Status:** Approved, ready for implementation planning

## Problem

BIFlow's dashboard shows KPI values and insights, but nothing lets you verify
*which rows* produced a number. The Auditor/XAI agent's `traceability_log`
and `validation_status` don't even reach the frontend today, and an
insight's only "explanation" is the human-readable description string
already baked in (e.g. "Revenue went from 11280.34 in 2018-07 to 3992.48 in
2018-08"). For an "Audit Console" whose whole premise is traceability, you
can't currently click through to the receipts.

## Goal

Clicking any KPI card (Overview tab) or any insight (Insights tab) reveals:
1. A trace summary — the KPI's formula, any month filter applied, and how
   many rows matched.
2. A table of the actual analytical-table rows that matched, capped at 50
   with a "showing 50 of N" note (no pagination in v1).

Breakdown bars (Breakdowns tab) are explicitly out of scope for this pass.

## Prerequisite fix

`agents/dashboard_agent/api.py`'s `run_pipeline` endpoint domain-scopes the
dashboard layout path (`dashboard_layout_<domain>.json`) but **not** the
analytical table path — every live-triggered run writes to the same shared
`data/processed/analytical_table.csv` regardless of domain. Drill-down reads
that file, so without this fix a domain's drill-down could silently show a
different domain's rows if another domain was run afterward. Fix: add an
`_analytical_path_for(domain)` helper (mirroring `_layout_path_for`) and pass
its result as `analytical_path` to `BIFlowOrchestrator(...)` in
`run_pipeline`, i.e. `data/processed/analytical_table_<domain>.csv`.

## Backend design

### 1. Single source of truth for "which rows count"

Each domain's `_compute_*_kpis` function in
`agents/kpi_semantic_agent/kpi_computation.py` already contains the boolean
filter for every KPI inline (e.g.
`non_canceled = df[df["order_status"] != "canceled"]`). Duplicating these
conditions in a new row-filter module would let the drill-down silently
drift from the actual KPI definition if one is ever edited without the
other.

New module `agents/kpi_semantic_agent/row_filters.py` defines, per domain, a
`{kpi_name: (df) -> df}` map of the same filters, and a
`filter_rows(df, business_domain, kpi_name, month=None) -> pd.DataFrame`
entrypoint that looks up the KPI's filter, applies it, and — if `month` is
given and the domain has a date column — further filters to that `YYYY-MM`.
`_compute_ecommerce_kpis`/`_compute_banking_kpis`/`_compute_telco_kpis` (and
`monthly_trends.py`'s per-domain functions, which already bucket by month)
are refactored to call `filter_rows(...)` instead of inlining the same
conditions, so there is exactly one definition per KPI.

Per-domain filter map (mirrors the existing inline conditions where one
exists; `average_review_score` and `average_account_balance` currently rely
on `pandas.mean()` silently skipping `NaN` rather than an explicit filter —
`filter_rows` makes that explicit as `.notna()` so the drill-down table
doesn't show rows that didn't actually contribute to the average. This
doesn't change either KPI's computed value, only which rows the drill-down
displays):

| Domain | KPI | Filter |
|---|---|---|
| e-commerce | `total_revenue`, `average_order_value` | `order_status != "canceled"` |
| e-commerce | `order_count` | none (all rows) |
| e-commerce | `average_review_score` | `review_score.notna()` |
| e-commerce | `on_time_delivery_rate` | `order_delivered_customer_date.notna()` |
| banking | `total_transaction_volume`, `average_transaction_value` | `type == "PRIJEM"` |
| banking | `transaction_count` | none |
| banking | `average_account_balance` | `balance.notna()` |
| banking | `loan_good_standing_rate` | `loan_status.notna()` |
| telco | all four KPIs | none (each is a whole-table count/mean; no meaningful subset) |

Date column for month filtering: `order_purchase_timestamp` (e-commerce),
`date` (banking), none (telco — its insights never carry a month anyway).

### 2. `Insight.month` field

`shared/schemas/data_contracts.py`'s `Insight` gets an optional
`month: str | None = None` (backward compatible — existing construction
sites are unaffected). `generate_monthly_trend_insights` in
`agents/bi_analyst_agent/insight_generator.py` sets it to
`trend["latest_month"]`; threshold insights (`generate_insights`) and the
telco "no trends available" insight leave it `None`.

### 3. `GET /api/drilldown?domain=&kpi=&month=`

- Validates `domain` against `ALLOWED_DOMAINS` (404 otherwise, same as the
  existing endpoints).
- Resolves the domain's analytical CSV via `_analytical_path_for` (404 with
  "no dashboard data yet" if it doesn't exist yet, matching
  `/api/dashboard`'s existing behavior).
- Loads the CSV into an in-process cache keyed by `(path, mtime)` so repeat
  drill-down clicks during a session don't re-read a potentially
  million-row file from disk each time; a new pipeline run changes the
  file's mtime and invalidates the cache entry.
- Calls `filter_rows(df, domain, kpi, month)`; an unknown `kpi` name raises
  `KeyError` inside `filter_rows`, translated to a 404.
- Returns `{"total_rows": int, "columns": [...], "rows": [...]}`, `rows`
  capped to the first 50 matches (`page = matching.head(50)`), serialized
  through `to_json` so NaN/Timestamp values round-trip safely.

## Frontend design

### 1. `DrillDownPanel.tsx` (new, shared)

Props: `domain`, `kpiName`, `month?`, `formula?` (the KPI's existing
`explanation` text, reused as the trace summary's formula line). Starts
collapsed; fetching only happens when a "View underlying rows ▸" toggle is
clicked (lazy — avoids hitting `/api/drilldown` for every rendered KPI card
or insight, most of which nobody will inspect). Renders a loading state,
then the trace summary line (formula, month filter if present, "N rows
matched, showing first 50") followed by a horizontally-scrollable table.

### 2. KPI cards (Overview tab)

`KpiDetail.tsx` gains a `domain` prop (threaded from `page.tsx`'s
`data.business_domain`, which is already fetched) and mounts
`<DrillDownPanel domain={domain} kpiName={card.name} formula={card.explanation} />`
inside its existing panel, below the trend chart.

### 3. Insights tab

Each insight `<li>` becomes a `<button>` (same interaction pattern already
used for KPI cards in Overview), toggling a `selectedInsightIndex` state.
The selected insight expands inline to show
`<DrillDownPanel domain={...} kpiName={insight.related_kpi} month={insight.month} formula={...} />`.
Insights with an empty `related_kpi` (telco's "no trends available" note)
render as plain non-interactive list items, same as today — there's nothing
to trace for those.

### 4. Types

`types.ts`'s `Insight` gains `month?: string | null`; a new
`DrillDownResponse { total_rows: number; columns: string[]; rows: Record<string, unknown>[] }`
type is added for the fetch result.

## Testing

- Backend: unit tests for `row_filters.filter_rows` per domain (each KPI's
  filter matches the existing aggregate computation's row count; month
  filtering narrows correctly; unknown KPI raises `KeyError`). API tests for
  `/api/drilldown` (200 with rows for a known KPI, month-scoped result is a
  subset of the unscoped one, unknown domain/KPI → 404, row cap enforced at
  50 with correct `total_rows`). Existing `kpi_computation.py` tests must
  keep passing unchanged (the refactor shouldn't change computed values).
- Frontend: component tests for `DrillDownPanel` (collapsed by default,
  fetches only on toggle, loading/error/empty states, table renders
  returned rows), and updated tests for the Insights tab (rows are buttons
  now, clicking expands the panel, empty-`related_kpi` insights stay
  non-interactive) and `KpiDetail` (drill-down toggle present, domain
  threaded through).

## Explicitly out of scope (v1)

- Breakdown-tab (per-category/region bar) drill-down.
- Pagination beyond the first 50 rows.
- Persisting/deep-linking to an open drill-down (e.g. via URL).

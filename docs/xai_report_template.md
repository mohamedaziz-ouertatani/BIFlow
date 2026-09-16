# XAI Report Template

**Owner:** Person E (BI Auditor/XAI Agent)

Used to render `shared.schemas.data_contracts.AuditReport` into a
human-readable explainability report.

## Validation status

<validation_status>

## Explanations

For each KPI or insight requiring explanation:

### <KPI name or Insight title>

<explanation text>

## Traceability log

- <trace event 1>
- <trace event 2>

---

## Example: rendered output

The example below is the real `AuditReport` produced by running the full
pipeline (`DataEngineeringAgent` → `KPISemanticAgent` → `BIAnalystAgent` →
`DashboardAgent` → `AuditorXAIAgent`) against `data/sample/olist`, the
sample dataset also used in `tests/test_auditor_xai_agent.py`.

### Validation status

`passed_with_warnings`

### Explanations

#### total_revenue

Total revenue from non-canceled order items. Computed as
`sum(price) where order_status != 'canceled'` = 68048.73.

#### average_order_value

Average amount spent per non-canceled order. Computed as
`total_revenue / count(distinct order_id where order_status != 'canceled')` = 137.47.

#### order_count

Total number of distinct orders, across all statuses. Computed as
`count(distinct order_id)` = 498.

#### average_review_score

Average customer review score (1-5) across orders with a review. Computed as
`mean(review_score)` = 3.91.

#### on_time_delivery_rate

Share of delivered orders that arrived on or before the estimated date.
Computed as
`count(order_delivered_customer_date <= order_estimated_delivery_date) / count(order_delivered_customer_date is not null)` = 0.94.

#### Strong on-time delivery

on_time_delivery_rate is 0.94 (at or above the 0.9 threshold).

#### Review scores below target

average_review_score is 3.91 (below the 4.0 threshold).

#### Revenue decreasing month-over-month

Revenue went from 11280.34 in 2018-07 to 3992.48 in 2018-08 (-64.6%).

#### Order volume increasing month-over-month

Order volume went from 31.0 in 2018-07 to 34.0 in 2018-08 (+9.7%).

#### Review score increasing month-over-month

Review score went from 4.29 in 2018-07 to 4.29 in 2018-08 (+0.1%).

### Traceability log

- data_engineering: produced `analytical.csv` (5754 rows profiled, 7 transformations applied)
- kpi_semantic: computed 5 KPIs
- bi_analyst: generated 5 insights
- dashboard: published to http://localhost:3000 (2 visualizations)

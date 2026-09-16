# KPI Catalog

**Owner:** Person B (BI Semantic & KPI Agent)

KPIs defined in `agents/kpi_semantic_agent/kpi_definitions.py` for the
`e-commerce` business domain (Olist), computed by
`agents/kpi_semantic_agent/kpi_computation.py`.

## total_revenue

- **Formula:** `sum(price) where order_status != 'canceled'`
- **Description:** Total revenue from non-canceled order items.
- **Dimensions:** `category`, `state` (see Breakdowns below)
- **Business domain(s):** e-commerce

## average_order_value

- **Formula:** `total_revenue / count(distinct order_id where order_status != 'canceled')`
- **Description:** Average amount spent per non-canceled order.
- **Dimensions:** `category`, `state`
- **Business domain(s):** e-commerce

## order_count

- **Formula:** `count(distinct order_id)`
- **Description:** Total number of distinct orders, across all statuses (including canceled).
- **Dimensions:** `category`, `state`
- **Business domain(s):** e-commerce

## average_review_score

- **Formula:** `mean(review_score)`
- **Description:** Average customer review score (1-5) across orders with a review.
- **Dimensions:** `category`, `state`
- **Business domain(s):** e-commerce

## on_time_delivery_rate

- **Formula:** `count(order_delivered_customer_date <= order_estimated_delivery_date) / count(order_delivered_customer_date is not null)`
- **Description:** Share of delivered orders that arrived on or before the estimated date. Only considers orders that have actually been delivered.
- **Dimensions:** `category`, `state`
- **Business domain(s):** e-commerce

## Breakdowns

Every KPI above lists `category` and `state` in `KPIDefinition.dimensions`.
`KPISemanticAgent` computes both breakdowns for every KPI and returns them on
`KPICatalog.breakdowns`: `{dimension: {group_value: {kpi_name: value}}}`,
e.g. `breakdowns["state"]["SP"]["total_revenue"]`.

- `category` groups by `product_category_name_english`
  (`agents/kpi_semantic_agent/agent.py::DIMENSION_COLUMNS`)
- `state` groups by `customer_state`

Since the analytical table is at order-item grain, an order spanning
multiple categories is attributed to each of them — the same caveat that
already applies to the overall `total_revenue`/`order_count` formulas above,
just visible per-group instead of only in aggregate.

`KPICatalog.computed_values` (the overall, non-broken-down values) is
unchanged — existing consumers (BI Analyst, Dashboard, Auditor/XAI agents)
don't need to change to keep working; `breakdowns` is additive.

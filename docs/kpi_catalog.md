# KPI Catalog

**Owner:** Person B (BI Semantic & KPI Agent)

KPIs defined in `agents/kpi_semantic_agent/kpi_definitions.py` for the
`e-commerce` business domain (Olist), computed by
`agents/kpi_semantic_agent/kpi_computation.py`.

## total_revenue

- **Formula:** `sum(price) where order_status != 'canceled'`
- **Description:** Total revenue from non-canceled order items.
- **Dimensions:** none yet (see TODO below)
- **Business domain(s):** e-commerce

## average_order_value

- **Formula:** `total_revenue / count(distinct order_id where order_status != 'canceled')`
- **Description:** Average amount spent per non-canceled order.
- **Dimensions:** none yet
- **Business domain(s):** e-commerce

## order_count

- **Formula:** `count(distinct order_id)`
- **Description:** Total number of distinct orders, across all statuses (including canceled).
- **Dimensions:** none yet
- **Business domain(s):** e-commerce

## average_review_score

- **Formula:** `mean(review_score)`
- **Description:** Average customer review score (1-5) across orders with a review.
- **Dimensions:** none yet
- **Business domain(s):** e-commerce

## on_time_delivery_rate

- **Formula:** `count(order_delivered_customer_date <= order_estimated_delivery_date) / count(order_delivered_customer_date is not null)`
- **Description:** Share of delivered orders that arrived on or before the estimated date. Only considers orders that have actually been delivered.
- **Dimensions:** none yet
- **Business domain(s):** e-commerce

## TODO
- [ ] Add category/state breakdowns (via `KPIDefinition.dimensions`) once needed downstream

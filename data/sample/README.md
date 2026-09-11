# Sample data — Olist Brazilian E-Commerce

A small, git-friendly sample of the [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
dataset, used by the end-to-end test and each agent's own tests.

## Contents (`olist/`)

500 randomly sampled orders (seed=42) plus every row in the related tables
that those orders reference (customers, order items, payments, reviews,
products, sellers). `olist_geolocation_dataset.csv` is capped to 3 rows per
zip-code prefix since it's a lookup table, not order-linked.

| File | Rows |
|---|---|
| `olist_orders_dataset.csv` | 500 |
| `olist_customers_dataset.csv` | 500 |
| `olist_order_items_dataset.csv` | 568 |
| `olist_order_payments_dataset.csv` | 515 |
| `olist_order_reviews_dataset.csv` | 500 |
| `olist_products_dataset.csv` | 490 |
| `olist_sellers_dataset.csv` | 320 |
| `olist_geolocation_dataset.csv` | 2,290 |
| `product_category_name_translation.csv` | 71 (full, unfiltered lookup table) |

## Full dataset

The full dataset lives in `data/raw/olist/` (gitignored — not committed).
Point `RawDatasetRef.dataset_path` at that directory for full runs, and at
`data/sample/olist/` for fast local dev/tests.

## Regenerating the sample

The sample was built by randomly selecting 500 orders and filtering every
other table to rows referenced by those orders (foreign-key closure). See
git history / ask the Data Engineering Agent owner for the generation
script if it needs to be rebuilt with a different size or seed.

# Multi-domain support: adding a banking domain

Date: 2026-09-16
Status: approved design, pending implementation plan

## Goal

BIFlow's `business_domain` field already flows through every shared
contract (`RawDatasetRef`, `CleanedDataset`, ...) but today only
`kpi_definitions.py` actually branches on it — every other agent hardcodes
Olist/e-commerce table names, join logic, and KPI math. This spec
generalizes each agent's domain-specific logic into a per-domain registry
(the same dict-lookup pattern `kpi_definitions.py` already uses) and
implements a second, fully working domain — **banking**, using the public
[Berka dataset](https://sorry.vse.cz/~berka/challenge/PAST/) (Czech bank,
PKDD'99 Discovery Challenge) — end to end through profiling, cleaning,
ETL, KPIs, trends, and the dashboard.

Source data lives at `data/raw/berka/` (not yet committed —
gitignored like `data/raw/olist/`): `account.csv`, `card.csv`,
`client.csv`, `disp.csv`, `district.csv`, `loan.csv`, `order.csv`,
`trans.csv` (~1.06M rows, semicolon-delimited, quoted strings).

## What does NOT change

`dashboard_agent` (`agent.py` + `layout_builder.py`), `auditor_xai_agent`,
`orchestrator`, and `shared/schemas/data_contracts.py` are already fully
domain-agnostic — they drive entirely off whatever `KPIDefinition`s and
computed values a domain produces. No changes needed there. Multi-domain
selection continues to work purely through the existing
`business_domain` CLI arg / constructor param — no new contracts, no new
CLI flags.

## Domain registry pattern

Every agent module that currently hardcodes e-commerce specifics gets a
`_BY_DOMAIN` dict keyed by `business_domain` string, mirroring
`kpi_definitions.py`'s existing `_KPIS_BY_DOMAIN`. A domain string not in
the dict raises `KeyError` (same behavior `get_kpi_definitions` already
has today — no new validation/fallback machinery).

## Banking analytical grain

One row per **transaction** (`trans.csv`), the finest-grained banking
entity — direct analog to e-commerce's order-item grain. Left-joined to:

- `account.csv` on `account_id` → `district_id`, `frequency`
- `district.csv` on `district_id` → region name (column `A3`, renamed to
  `region` during the join, analog to `customer_state`)
- `loan.csv` on `account_id` → `status` (renamed `loan_status`); most
  accounts have no loan, so this is `NaN` for them, same shape as
  `average_review_score`'s optional review join in e-commerce

`client.csv`, `disp.csv`, `card.csv`, `order.csv` (standing orders) are
loaded and profiled by `profiler.py` like every raw table, but — like
`geolocation.csv` in the e-commerce domain today — are **not** joined
into the analytical table, since none of the five KPIs below need them.
Decoding `client.birth_number` (which encodes birth date + gender) is
explicitly out of scope; nothing downstream needs it.

## Cleaning rules (banking)

1. **Datetime parsing.** Banking dates are `YYMMDD` integers (e.g.
   `930101`), not ISO strings, and the column names (`date`, `issued`)
   don't match e-commerce's `_date`/`_at` suffix heuristic. Banking gets
   its own explicit `(table, column) -> strptime format` map instead of
   reusing the suffix heuristic:
   - `account.date`, `trans.date`, `loan.date`: `"%y%m%d"`
   - `card.issued`: `"%y%m%d %H:%M:%S"`
2. **`trans.type` normalization.** The raw data has three type values
   instead of the documented two: `PRIJEM` (118,010 rows), `VYDAJ`
   (177,575 rows), and `VYBER` (4,415 rows) — `VYBER` is a known artifact
   in this dataset (a legacy withdrawal label that should be `VYDAJ`).
   Cleaning rule: normalize `VYBER` → `VYDAJ`, logged as a transformation
   (analogous to today's `products.product_category_name` fill-with-
   `"unknown"` rule).
3. Generic rules (dedup, drop-duplicates) already apply unchanged.

No row-filtering rule is needed for `amount`/`balance` — negative
`balance` is legitimate (overdraft), and `amount` is always positive in
this dataset (direction is carried by `type`), unlike Olist's `price`
column which needed a null/negative guard.

## Banking KPIs (direct analogs of the 5 e-commerce KPIs)

| Banking KPI | Formula | E-commerce analog |
|---|---|---|
| `total_transaction_volume` | `sum(amount)` where `type == "PRIJEM"` | `total_revenue` |
| `average_transaction_value` | `total_transaction_volume / count(distinct trans_id where type == "PRIJEM")` | `average_order_value` |
| `transaction_count` | `count(distinct trans_id)`, all types | `order_count` |
| `average_account_balance` | `mean(balance)` over the analytical table | `average_review_score` |
| `loan_good_standing_rate` | `count(loan_status in ("A","C")) / count(loan_status.notna())` | `on_time_delivery_rate` |

`loan_good_standing_rate` (not `loan_default_rate`) is deliberately framed
so **higher = healthier**, matching `on_time_delivery_rate`'s direction —
`trend_detection.py`'s threshold check is a flat `value >= threshold`, so
keeping the same direction avoids adding branching logic there.

Breakdown dimensions (`KPIDefinition.dimensions`, mirrors `category`/
`state`):
- `region` → analytical column `region`
- `transaction_type` → analytical column `type_label`, an English
  translation of `type` (`PRIJEM` → `"credit"`, `VYDAJ` → `"debit"`),
  built the same way e-commerce translates `product_category_name` via
  `category_translation.csv` (here it's a 2-entry dict, no file needed)

`average_account_balance` and `loan_good_standing_rate` are computed
directly over the transaction-grain analytical table (not deduplicated
to one row per account first), so accounts with more transactions
implicitly weigh more heavily — this mirrors `average_review_score`'s
existing behavior in e-commerce (also computed over item-grain rows
without deduplicating to one row per order), kept for consistency rather
than "fixed" into a per-account average, to avoid diverging in
sophistication between the two domains.

Real data stats behind these choices (sampled from `trans.csv`):
`loan.status` counts are C=403, A=203, D=45, B=31 → good-standing rate
≈ 88.9% (threshold below), `balance` median ≈ 30,930 / mean ≈ 35,831
(threshold below).

## Trend/insight thresholds (banking)

`trend_detection.py` `THRESHOLDS` gets a banking entry:
- `loan_good_standing_rate: 0.85`
- `average_account_balance: 30000`

`monthly_trends.py` gets a banking implementation bucketing by month
(from `trans.date`) computing `total_transaction_volume`,
`transaction_count`, `average_account_balance` per month — same shape as
today's revenue/order_count/review_score triple, dispatched by domain
the same way `kpi_computation.py` will be.

`insight_generator.py`'s `TITLES`/`MONTHLY_TREND_LABELS` dicts get
banking entries for polish (e.g. `("loan_good_standing_rate",
"concerning"): "Loan default rate above target"`) — additive only, since
both already fall back to a generic `f"{kpi_name}: {status}"` label when
a key is missing, so this isn't required for correctness.

## Testing

Each modified module (`profiler`, `cleaner`, `etl`, `kpi_computation`,
`kpi_semantic_agent/agent`, `trend_detection`, `monthly_trends`) gets a
banking-domain test alongside its existing e-commerce test, same file,
same pattern as today. A trimmed `data/sample/banking/` fixture (a few
hundred transactions across a handful of accounts, spanning at least two
calendar months so monthly-trend tests have real data to compare) gets
committed, mirroring `data/sample/olist/`'s role — tests never load the
full ~1M-row `trans.csv`. One end-to-end pipeline run against
`data/sample/banking/` (`python -m orchestrator data/sample/banking
banking --no-postgres`) is added to `tests/` alongside the existing
e-commerce integration test.

## Out of scope

- Decoding `client.birth_number` into birthdate/gender
- Joining `card.csv`/`order.csv` (standing orders) into the analytical
  table — not needed by any of the 5 KPIs
- Any change to `dashboard_agent`, `auditor_xai_agent`, `orchestrator`,
  or the frontend
- A third domain, or a generic N-domain plugin interface beyond the
  dict-registry pattern (YAGNI for 2 domains — see approaches considered
  below)

## Approaches considered

- **Chosen: per-agent dict registries**, extending the pattern already
  proven in `kpi_definitions.py`. Least invasive, keeps each agent's
  domain config colocated with its own logic, respects the existing
  "agents only talk to the orchestrator" boundary.
- **Rejected: centralized `DomainSpec` in `shared/`.** Less duplication,
  but couples every agent to one shared mega-config and blurs agent
  independence.
- **Rejected: abstract `DomainAdapter` plugin classes.** Most extensible
  for N domains, but turns simple functions into class hierarchies
  everywhere — more churn than a 2-domain case justifies.

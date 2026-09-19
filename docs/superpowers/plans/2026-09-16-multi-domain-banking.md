# Multi-domain support (banking) Implementation Plan

> **Status: implemented and merged.** The steps below were ticked in bulk after the
> feature shipped, not one at a time as it was built.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Generalize BIFlow's per-agent hardcoded Olist/e-commerce logic into a per-domain dict-registry pattern, and implement a second, fully working domain — banking, using the Berka dataset — end to end through profiling, cleaning, ETL, KPIs, trends, and the dashboard.

**Architecture:** Extend the dict-lookup pattern `kpi_definitions.py` already uses (`_KPIS_BY_DOMAIN`) into every other agent module that currently hardcodes e-commerce specifics: `profiler.py`, `cleaner.py`, `etl.py`, `kpi_computation.py`, `kpi_semantic_agent/agent.py`, `monthly_trends.py`. Two modules (`trend_detection.py`, `insight_generator.py`) need no dispatch at all — their lookup keys are KPI names, which never collide across domains, so banking entries are additive to the same flat dict. `dashboard_agent`, `auditor_xai_agent`, `orchestrator`, and the frontend need zero changes — confirmed by reading their source; they drive entirely off whatever `KPIDefinition`s and computed values a domain produces.

**Tech Stack:** Python 3.13, pandas, pydantic, pytest. Banking source data: `data/raw/berka/` (Berka/PKDD'99 Czech bank dataset, semicolon-delimited CSVs, not yet committed — gitignored like `data/raw/olist/`).

**Spec:** [docs/superpowers/specs/2026-09-16-multi-domain-banking-design.md](../specs/2026-09-16-multi-domain-banking-design.md)

## Global Constraints

- Every function whose behavior differs by domain takes an explicit `business_domain: str` parameter — no domain is ever inferred or defaulted.
- An unrecognized `business_domain` raises `KeyError` (dict `[...]` lookup, not `.get()`) — matches `get_kpi_definitions`'s existing behavior. No new validation/fallback machinery.
- Banking KPI directions must match their e-commerce analog (higher = healthier), since `trend_detection.py`'s threshold check is a flat `value >= threshold` with no direction flag.
- No changes to `agents/dashboard_agent/`, `agents/auditor_xai_agent/`, `orchestrator/`, `shared/schemas/data_contracts.py`, or `frontend/` — verified domain-agnostic already.
- Banking analytical grain: one row per transaction (`trans.csv`), joined left to `account` (district_id, frequency), `district` (region name), `loan` (status) only — `client`/`disp`/`card`/`order.csv` are loaded/profiled but not joined (mirrors `geolocation.csv` in e-commerce today).

---

## File Structure

**New files:**
- `scripts/build_banking_sample.py` — one-off script generating `data/sample/banking/` from `data/raw/berka/`
- `data/sample/banking/{account,client,disp,district,loan,card,order,trans}.csv` — generated sample data (committed)

**Modified files:**
- `data/sample/README.md` — add a Banking section
- `agents/data_engineering_agent/profiler.py` — per-domain table filenames + CSV separator
- `agents/data_engineering_agent/cleaner.py` — per-domain datetime formats + cleaning rules
- `agents/data_engineering_agent/etl.py` — per-domain analytical table join
- `agents/data_engineering_agent/agent.py` — thread `business_domain` through
- `agents/data_engineering_agent/tests/test_profiler.py`, `test_cleaner.py`, `test_etl.py`, `test_data_engineering_agent.py`
- `agents/kpi_semantic_agent/kpi_definitions.py` — add banking KPI definitions
- `agents/kpi_semantic_agent/kpi_computation.py` — per-domain KPI math
- `agents/kpi_semantic_agent/agent.py` — per-domain date/dimension columns
- `agents/kpi_semantic_agent/tests/test_kpi_definitions.py`, `test_kpi_computation.py`, `test_kpi_semantic_agent.py`
- `agents/bi_analyst_agent/trend_detection.py` — add banking thresholds (flat dict)
- `agents/bi_analyst_agent/monthly_trends.py` — per-domain monthly trends
- `agents/bi_analyst_agent/insight_generator.py` — add banking labels (flat dicts)
- `agents/bi_analyst_agent/agent.py` — pass `business_domain` through
- `agents/bi_analyst_agent/tests/test_trend_detection.py`, `test_monthly_trends.py`, `test_insight_generator.py`, `test_bi_analyst_agent.py`
- `tests/test_end_to_end.py` — add banking pipeline run

---

### Task 1: Generate the banking sample dataset

**Files:**
- Create: `scripts/build_banking_sample.py`
- Create: `data/sample/banking/account.csv`, `client.csv`, `disp.csv`, `district.csv`, `loan.csv`, `card.csv`, `order.csv`, `trans.csv`
- Modify: `data/sample/README.md`

**Interfaces:**
- Produces: `data/sample/banking/` directory with all 8 Berka tables, semicolon-delimited, a subset of accounts from `data/raw/berka/` selected with `random_state=42`. Every later task's banking tests read from this directory the same way `data/sample/olist` is used today.

This is a data-prep task (no application code), so it has no failing-test step — verification is a direct row-count/column check instead of pytest.

- [x] **Step 1: Write the sample-generation script**

```python
"""One-off script: builds data/sample/banking/ from data/raw/berka/.

Mirrors the role of data/sample/olist/: a small, git-friendly subset used
by tests and local dev. Selects a fixed random sample of accounts (seed=42)
plus every row in related tables that those accounts reference -- same
approach as the Olist sample's order-based selection.

Run once: `python scripts/build_banking_sample.py`
"""

import os

import pandas as pd

RAW_DIR = "data/raw/berka"
SAMPLE_DIR = "data/sample/banking"
SEED = 42
N_ACCOUNTS = 25


def main() -> None:
    account = pd.read_csv(os.path.join(RAW_DIR, "account.csv"), sep=";")
    disp = pd.read_csv(os.path.join(RAW_DIR, "disp.csv"), sep=";")
    client = pd.read_csv(os.path.join(RAW_DIR, "client.csv"), sep=";")
    district = pd.read_csv(os.path.join(RAW_DIR, "district.csv"), sep=";")
    loan = pd.read_csv(os.path.join(RAW_DIR, "loan.csv"), sep=";")
    card = pd.read_csv(os.path.join(RAW_DIR, "card.csv"), sep=";")
    order = pd.read_csv(os.path.join(RAW_DIR, "order.csv"), sep=";")
    trans = pd.read_csv(os.path.join(RAW_DIR, "trans.csv"), sep=";")

    sampled_accounts = account.sample(n=N_ACCOUNTS, random_state=SEED)
    account_ids = set(sampled_accounts["account_id"])

    sampled_trans = trans[trans["account_id"].isin(account_ids)]
    sampled_disp = disp[disp["account_id"].isin(account_ids)]
    sampled_loan = loan[loan["account_id"].isin(account_ids)]
    sampled_card = card[card["disp_id"].isin(sampled_disp["disp_id"])]
    sampled_order = order[order["account_id"].isin(account_ids)]

    client_ids = set(sampled_disp["client_id"])
    sampled_client = client[client["client_id"].isin(client_ids)]

    district_ids = set(sampled_accounts["district_id"]) | set(sampled_client["district_id"])
    sampled_district = district[district["A1"].isin(district_ids)]

    os.makedirs(SAMPLE_DIR, exist_ok=True)
    tables = {
        "account": sampled_accounts,
        "client": sampled_client,
        "disp": sampled_disp,
        "district": sampled_district,
        "loan": sampled_loan,
        "card": sampled_card,
        "order": sampled_order,
        "trans": sampled_trans,
    }
    for name, df in tables.items():
        df.to_csv(os.path.join(SAMPLE_DIR, f"{name}.csv"), sep=";", index=False)
        print(f"{name}: {len(df)} rows")

    months = pd.to_datetime(sampled_trans["date"].astype(str), format="%y%m%d").dt.to_period("M")
    print(f"trans spans {months.nunique()} distinct months: {sorted(months.unique().astype(str))}")


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Run the script and verify output**

Run: `python scripts/build_banking_sample.py`

Expected: prints row counts for all 8 tables, `trans` has at least several hundred rows, and "spans N distinct months" reports N >= 2 (required for the monthly-trend tests in Task 10 to have real data to compare — if N < 2, increase `N_ACCOUNTS` and rerun).

- [x] **Step 3: Update the sample data README**

Add to `data/sample/README.md` (append after the existing "Full dataset" section):

```markdown
## Contents (`banking/`)

A random sample of 25 accounts (seed=42) from the [Berka dataset](https://sorry.vse.cz/~berka/challenge/PAST/)
(Czech bank, PKDD'99 Discovery Challenge) plus every row in related tables
that those accounts reference, generated by `scripts/build_banking_sample.py`.
Unlike the Olist tables, these are semicolon-delimited (`sep=";"`), matching
the raw Berka format.

| File | Rows |
|---|---|
| `account.csv` | 25 |
| `trans.csv` | see script output |
| `disp.csv` | see script output |
| `loan.csv` | see script output |
| `card.csv` | see script output |
| `order.csv` | see script output |
| `client.csv` | see script output |
| `district.csv` | see script output |

## Full banking dataset

The full dataset lives in `data/raw/berka/` (gitignored — not committed).
Point `RawDatasetRef.dataset_path` at that directory for full runs
(`business_domain="banking"`), and at `data/sample/banking/` for fast
local dev/tests.
```

Replace the "see script output" placeholders with the actual counts printed in Step 2.

- [x] **Step 4: Confirm `data/raw/berka` stays gitignored, commit the sample**

Run: `git check-ignore data/raw/berka/account.csv` — expected: prints the path (confirms it's ignored, same as `data/raw/olist`). If it doesn't print anything, check `.gitignore` for a `data/raw/` pattern before continuing.

```bash
git add scripts/build_banking_sample.py data/sample/banking/ data/sample/README.md
git commit -m "Add banking sample dataset (Berka, 25 accounts)"
```

---

### Task 2: `profiler.py` — per-domain table loading

**Files:**
- Modify: `agents/data_engineering_agent/profiler.py`
- Test: `agents/data_engineering_agent/tests/test_profiler.py`

**Interfaces:**
- Consumes: `data/sample/banking/` from Task 1.
- Produces: `load_all_tables(dataset_dir: str, business_domain: str) -> dict[str, pd.DataFrame]` (signature changed — now requires `business_domain`). `profile_dataset(raw_dataset: RawDatasetRef) -> ProfilingReport` (signature unchanged, now passes `raw_dataset.business_domain` through internally). Later tasks (`agent.py` in Task 5) call `load_all_tables(dataset_path, business_domain)`.

- [x] **Step 1: Update `test_load_all_tables_loads_every_olist_table_by_logical_name` for the new signature, add a banking test**

In `agents/data_engineering_agent/tests/test_profiler.py`, change:

```python
def test_load_all_tables_loads_every_olist_table_by_logical_name():
    tables = load_all_tables(SAMPLE_DIR)
```

to:

```python
def test_load_all_tables_loads_every_olist_table_by_logical_name():
    tables = load_all_tables(SAMPLE_DIR, "e-commerce")
```

Also update `test_profile_dataset_aggregates_all_tables_into_one_report`'s helper call:

```python
    tables = load_all_tables(SAMPLE_DIR)
```

to:

```python
    tables = load_all_tables(SAMPLE_DIR, "e-commerce")
```

Add at the end of the file:

```python
BANKING_SAMPLE_DIR = "data/sample/banking"


def test_load_all_tables_loads_every_banking_table_by_logical_name():
    tables = load_all_tables(BANKING_SAMPLE_DIR, "banking")
    assert set(tables.keys()) == {
        "account",
        "client",
        "disp",
        "district",
        "loan",
        "card",
        "order",
        "trans",
    }
    assert len(tables["trans"]) > 0
    assert "account_id" in tables["trans"].columns


def test_profile_dataset_aggregates_banking_tables_into_one_report():
    raw = RawDatasetRef(
        dataset_path=BANKING_SAMPLE_DIR, dataset_name="berka_banking", business_domain="banking"
    )
    report = profile_dataset(raw)

    assert isinstance(report, ProfilingReport)
    tables = load_all_tables(BANKING_SAMPLE_DIR, "banking")
    assert report.n_rows == sum(len(df) for df in tables.values())
    assert "trans.trans_id" in report.column_types
    assert "account.account_id" in report.column_types
```

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest agents/data_engineering_agent/tests/test_profiler.py -v`
Expected: FAIL — `load_all_tables() missing 1 required positional argument: 'business_domain'` and `NameError`/`KeyError` for the new banking tests.

- [x] **Step 3: Implement per-domain table loading**

Replace the top of `agents/data_engineering_agent/profiler.py`:

```python
"""Dataset profiling logic for the Data Engineering Agent."""

import os
from typing import Any

import pandas as pd

from shared.schemas.data_contracts import ProfilingReport, RawDatasetRef

TABLE_FILENAMES_BY_DOMAIN = {
    "e-commerce": {
        "orders": "olist_orders_dataset.csv",
        "customers": "olist_customers_dataset.csv",
        "order_items": "olist_order_items_dataset.csv",
        "order_payments": "olist_order_payments_dataset.csv",
        "order_reviews": "olist_order_reviews_dataset.csv",
        "products": "olist_products_dataset.csv",
        "sellers": "olist_sellers_dataset.csv",
        "geolocation": "olist_geolocation_dataset.csv",
        "category_translation": "product_category_name_translation.csv",
    },
    "banking": {
        "account": "account.csv",
        "client": "client.csv",
        "disp": "disp.csv",
        "district": "district.csv",
        "loan": "loan.csv",
        "card": "card.csv",
        "order": "order.csv",
        "trans": "trans.csv",
    },
}

CSV_SEP_BY_DOMAIN = {
    "e-commerce": ",",
    "banking": ";",
}


def load_all_tables(dataset_dir: str, business_domain: str) -> dict[str, pd.DataFrame]:
    """Loads every table for business_domain from dataset_dir, keyed by logical table name."""
    filenames = TABLE_FILENAMES_BY_DOMAIN[business_domain]
    sep = CSV_SEP_BY_DOMAIN[business_domain]
    return {
        logical_name: pd.read_csv(os.path.join(dataset_dir, filename), sep=sep)
        for logical_name, filename in filenames.items()
    }
```

Leave `profile_table` unchanged. Update `profile_dataset`'s first line:

```python
def profile_dataset(raw_dataset: RawDatasetRef) -> ProfilingReport:
    """Profiles every table in raw_dataset.dataset_path and aggregates into one ProfilingReport."""
    tables = load_all_tables(raw_dataset.dataset_path, raw_dataset.business_domain)
```

(rest of the function body unchanged).

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest agents/data_engineering_agent/tests/test_profiler.py -v`
Expected: PASS (6 existing + 2 new tests)

- [x] **Step 5: Commit**

```bash
git add agents/data_engineering_agent/profiler.py agents/data_engineering_agent/tests/test_profiler.py
git commit -m "profiler.py: load tables per business_domain"
```

---

### Task 3: `cleaner.py` — per-domain cleaning rules

**Files:**
- Modify: `agents/data_engineering_agent/cleaner.py`
- Test: `agents/data_engineering_agent/tests/test_cleaner.py`

**Interfaces:**
- Produces: `clean_tables(tables: dict[str, pd.DataFrame], business_domain: str) -> tuple[dict[str, pd.DataFrame], list[str]]` (signature changed — now requires `business_domain`).

Banking dates are `YYMMDD` integers (e.g. `930101`), which don't match e-commerce's `_date`/`_at` suffix heuristic (column names are just `date`/`issued`), so banking gets an explicit `(table, column) -> strptime format` map instead.

- [x] **Step 1: Update existing cleaner tests for the new signature, add banking tests**

In `agents/data_engineering_agent/tests/test_cleaner.py`, add `"e-commerce"` as the second argument to all 4 existing `clean_tables(tables)` calls, e.g.:

```python
def test_clean_tables_drops_exact_duplicate_rows():
    tables = {
        "sellers": pd.DataFrame({"seller_id": ["a", "a", "b"], "seller_city": ["x", "x", "y"]})
    }
    cleaned, _ = clean_tables(tables, "e-commerce")
    assert len(cleaned["sellers"]) == 2
```

(apply the same `, "e-commerce"` change to the other 3 calls in that file).

Add at the end of the file:

```python
def test_clean_tables_parses_banking_yymmdd_date_columns():
    tables = {
        "trans": pd.DataFrame(
            {"trans_id": [1, 2], "account_id": [10, 10], "date": [930101, 930215], "amount": [100.0, 50.0]}
        )
    }
    cleaned, _ = clean_tables(tables, "banking")
    assert pd.api.types.is_datetime64_any_dtype(cleaned["trans"]["date"])
    assert cleaned["trans"]["date"].iloc[0] == pd.Timestamp("1993-01-01")


def test_clean_tables_parses_banking_card_issued_datetime_with_time_component():
    tables = {
        "card": pd.DataFrame({"card_id": [1], "disp_id": [9], "issued": ["931107 00:00:00"]})
    }
    cleaned, _ = clean_tables(tables, "banking")
    assert pd.api.types.is_datetime64_any_dtype(cleaned["card"]["issued"])
    assert cleaned["card"]["issued"].iloc[0] == pd.Timestamp("1993-11-07")


def test_clean_tables_normalizes_vyber_transaction_type_to_vydaj():
    tables = {
        "trans": pd.DataFrame(
            {
                "trans_id": [1, 2, 3],
                "account_id": [10, 10, 10],
                "date": [930101, 930102, 930103],
                "type": ["PRIJEM", "VYBER", "VYDAJ"],
            }
        )
    }
    cleaned, transformations = clean_tables(tables, "banking")
    assert list(cleaned["trans"]["type"]) == ["PRIJEM", "VYDAJ", "VYDAJ"]
    assert any("normalized 1 'VYBER' transaction types to 'VYDAJ'" in t for t in transformations)
```

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest agents/data_engineering_agent/tests/test_cleaner.py -v`
Expected: FAIL — `clean_tables() missing 1 required positional argument: 'business_domain'`

- [x] **Step 3: Implement per-domain cleaning**

Replace the full contents of `agents/data_engineering_agent/cleaner.py`:

```python
"""Data cleaning/quality logic for the Data Engineering Agent."""

import pandas as pd

DOMAIN_DATETIME_FORMATS = {
    "banking": {
        ("account", "date"): "%y%m%d",
        ("trans", "date"): "%y%m%d",
        ("loan", "date"): "%y%m%d",
        ("card", "issued"): "%y%m%d %H:%M:%S",
    },
}


def _apply_ecommerce_rules(
    name: str, df: pd.DataFrame, transformations: list[str]
) -> pd.DataFrame:
    if name == "order_items" and "price" in df.columns:
        before = len(df)
        df = df[df["price"].notna() & (df["price"] >= 0)]
        dropped = before - len(df)
        if dropped:
            transformations.append(
                f"{name}: dropped {dropped} order_items rows with null/negative price"
            )

    if name == "products" and "product_category_name" in df.columns:
        n_missing = int(df["product_category_name"].isna().sum())
        if n_missing:
            df["product_category_name"] = df["product_category_name"].fillna("unknown")
            transformations.append(
                f"{name}: filled missing product_category_name with 'unknown' "
                f"({n_missing} rows)"
            )

    return df


def _apply_banking_rules(name: str, df: pd.DataFrame, transformations: list[str]) -> pd.DataFrame:
    if name == "trans" and "type" in df.columns:
        n_bad = int((df["type"] == "VYBER").sum())
        if n_bad:
            df["type"] = df["type"].replace("VYBER", "VYDAJ")
            transformations.append(
                f"{name}: normalized {n_bad} 'VYBER' transaction types to 'VYDAJ'"
            )

    return df


def clean_tables(
    tables: dict[str, pd.DataFrame], business_domain: str
) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Applies data-quality cleaning rules to every table for business_domain.

    Returns the cleaned tables plus a list of human-readable transformations applied.
    """
    cleaned: dict[str, pd.DataFrame] = {}
    transformations: list[str] = []
    banking_date_formats = DOMAIN_DATETIME_FORMATS.get("banking", {})

    for name, df in tables.items():
        before = len(df)
        df = df.drop_duplicates()
        dropped = before - len(df)
        if dropped:
            transformations.append(f"{name}: dropped {dropped} exact duplicate rows")

        if business_domain == "e-commerce":
            date_cols = [
                c for c in df.columns if "timestamp" in c or c.endswith(("_date", "_at"))
            ]
            for col in date_cols:
                df[col] = pd.to_datetime(df[col])
            if date_cols:
                transformations.append(f"{name}: parsed {date_cols} as datetime")

            df = _apply_ecommerce_rules(name, df, transformations)

        elif business_domain == "banking":
            parsed_cols = []
            for (table, col), fmt in banking_date_formats.items():
                if table == name and col in df.columns:
                    df[col] = pd.to_datetime(df[col].astype(str), format=fmt)
                    parsed_cols.append(col)
            if parsed_cols:
                transformations.append(f"{name}: parsed {parsed_cols} as datetime")

            df = _apply_banking_rules(name, df, transformations)

        else:
            raise KeyError(business_domain)

        cleaned[name] = df

    return cleaned, transformations
```

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest agents/data_engineering_agent/tests/test_cleaner.py -v`
Expected: PASS (4 existing + 3 new tests)

- [x] **Step 5: Commit**

```bash
git add agents/data_engineering_agent/cleaner.py agents/data_engineering_agent/tests/test_cleaner.py
git commit -m "cleaner.py: per-domain cleaning rules, add banking date parsing + VYBER normalization"
```

---

### Task 4: `etl.py` — per-domain analytical table

**Files:**
- Modify: `agents/data_engineering_agent/etl.py`
- Test: `agents/data_engineering_agent/tests/test_etl.py`

**Interfaces:**
- Produces: `build_analytical_table(tables: dict[str, pd.DataFrame], business_domain: str) -> pd.DataFrame` and `run_etl(cleaned_tables: dict[str, pd.DataFrame], output_path: str, business_domain: str, database_url: str | None = None) -> tuple[str, list[str]]` (both signatures changed — `business_domain` added). Banking analytical columns produced: all of `trans.csv`'s columns (`trans_id`, `account_id`, `date`, `type`, `operation`, `amount`, `balance`, `k_symbol`, `bank`, `account`) plus `district_id`, `frequency` (from `account`), `region` (from `district`), `loan_status` (from `loan`), `type_label` (derived).

- [x] **Step 1: Update existing ETL tests for the new signature, add banking tests**

In `agents/data_engineering_agent/tests/test_etl.py`, add `"e-commerce"` as the second argument to every `build_analytical_table(tables)` call (4 occurrences) and every `run_etl(tables, output_path, ...)` call (2 occurrences: `run_etl(tables, output_path, "e-commerce")` and `run_etl(tables, output_path, "e-commerce", database_url=TEST_DATABASE_URL)`).

Add at the end of the file:

```python
def _banking_tables():
    return {
        "trans": pd.DataFrame(
            {
                "trans_id": [1, 2],
                "account_id": [10, 10],
                "date": pd.to_datetime(["1993-01-01", "1993-02-01"]),
                "type": ["PRIJEM", "VYDAJ"],
                "amount": [500.0, 200.0],
                "balance": [500.0, 300.0],
            }
        ),
        "account": pd.DataFrame({"account_id": [10], "district_id": [1], "frequency": ["POPLATEK MESICNE"]}),
        "district": pd.DataFrame({"A1": [1], "A2": ["Prague"], "A3": ["Prague region"]}),
        "loan": pd.DataFrame({"account_id": [10], "status": ["C"]}),
        "client": pd.DataFrame(columns=["client_id", "birth_number", "district_id"]),
        "disp": pd.DataFrame(columns=["disp_id", "client_id", "account_id", "type"]),
        "card": pd.DataFrame(columns=["card_id", "disp_id", "type", "issued"]),
        "order": pd.DataFrame(columns=["order_id", "account_id", "bank_to", "account_to", "amount", "k_symbol"]),
    }


def test_build_analytical_table_joins_banking_trans_with_account_and_district():
    result = build_analytical_table(_banking_tables(), "banking")
    assert len(result) == 2
    row = result[result["trans_id"] == 1].iloc[0]
    assert row["account_id"] == 10
    assert row["region"] == "Prague region"
    assert row["frequency"] == "POPLATEK MESICNE"


def test_build_analytical_table_joins_loan_status_for_accounts_with_a_loan():
    result = build_analytical_table(_banking_tables(), "banking")
    assert (result["loan_status"] == "C").all()


def test_build_analytical_table_leaves_loan_status_null_for_accounts_without_a_loan():
    tables = _banking_tables()
    tables["loan"] = pd.DataFrame(columns=["account_id", "status"])
    result = build_analytical_table(tables, "banking")
    assert result["loan_status"].isna().all()


def test_build_analytical_table_translates_transaction_type_to_english_label():
    result = build_analytical_table(_banking_tables(), "banking")
    labels = dict(zip(result["type"], result["type_label"]))
    assert labels == {"PRIJEM": "credit", "VYDAJ": "debit"}


def test_run_etl_writes_banking_analytical_table_to_output_path(tmp_path):
    output_path = str(tmp_path / "banking_analytical.csv")
    written_path, transformations = run_etl(_banking_tables(), output_path, "banking")
    assert written_path == output_path
    written = pd.read_csv(output_path)
    assert len(written) == 2
    assert "type_label" in written.columns
```

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest agents/data_engineering_agent/tests/test_etl.py -v -k "not postgres and not load_to_postgres"`
Expected: FAIL — `build_analytical_table() missing 1 required positional argument: 'business_domain'`

- [x] **Step 3: Implement per-domain ETL**

Replace the full contents of `agents/data_engineering_agent/etl.py`:

```python
"""ETL logic for the Data Engineering Agent: builds one analytical table per
business domain by joining that domain's cleaned tables together."""

import os

import pandas as pd
import sqlalchemy

TYPE_LABELS = {"PRIJEM": "credit", "VYDAJ": "debit"}

JOIN_DESCRIPTIONS = {
    "e-commerce": "joined order_items/orders/customers/payments/reviews/products/sellers",
    "banking": "joined trans/account/district/loan",
}


def build_analytical_table(tables: dict[str, pd.DataFrame], business_domain: str) -> pd.DataFrame:
    """Joins cleaned tables into one analytical table for business_domain."""
    if business_domain == "e-commerce":
        return _build_ecommerce_table(tables)
    if business_domain == "banking":
        return _build_banking_table(tables)
    raise KeyError(business_domain)


def _build_ecommerce_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Joins cleaned Olist tables into one order-item-level analytical table.

    Grain: one row per (order_id, order_item_id). Payments and reviews are
    aggregated to order level before joining since an order can have
    multiple payment installments or (rarely) multiple reviews.
    """
    result = tables["order_items"].merge(tables["orders"], on="order_id", how="left")
    result = result.merge(tables["customers"], on="customer_id", how="left")

    payments_per_order = (
        tables["order_payments"]
        .groupby("order_id")["payment_value"]
        .sum()
        .rename("total_payment_value")
    )
    result = result.merge(payments_per_order, on="order_id", how="left")

    reviews = tables["order_reviews"]
    if not reviews.empty:
        latest_reviews = (
            reviews.sort_values("review_creation_date")
            .groupby("order_id")
            .tail(1)[["order_id", "review_score"]]
        )
    else:
        latest_reviews = reviews[["order_id", "review_score"]]
    result = result.merge(latest_reviews, on="order_id", how="left")

    products = tables["products"].merge(
        tables["category_translation"], on="product_category_name", how="left"
    )
    result = result.merge(products, on="product_id", how="left")

    result = result.merge(tables["sellers"], on="seller_id", how="left")

    return result


def _build_banking_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Joins cleaned Berka tables into one transaction-level analytical table.

    Grain: one row per trans_id -- the banking analog to the e-commerce
    order-item grain. client/disp/card/order are loaded and profiled but
    not joined here, since none of the five banking KPIs need them.
    """
    result = tables["trans"].merge(
        tables["account"][["account_id", "district_id", "frequency"]],
        on="account_id",
        how="left",
    )

    district = tables["district"].rename(columns={"A1": "district_id", "A3": "region"})
    result = result.merge(district[["district_id", "region"]], on="district_id", how="left")

    loan_status = tables["loan"][["account_id", "status"]].rename(
        columns={"status": "loan_status"}
    )
    result = result.merge(loan_status, on="account_id", how="left")

    result["type_label"] = result["type"].map(TYPE_LABELS)

    return result


def run_etl(
    cleaned_tables: dict[str, pd.DataFrame],
    output_path: str,
    business_domain: str,
    database_url: str | None = None,
) -> tuple[str, list[str]]:
    """Builds the analytical table for business_domain and writes it to output_path as CSV.

    If database_url is given, also loads the analytical table into a
    Postgres table (`orders_analytical`) — the CSV remains the interchange
    format between agents; Postgres is an additional persistence sink.

    Returns the output path and a list of human-readable transformations applied.
    """
    analytical_table = build_analytical_table(cleaned_tables, business_domain)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    analytical_table.to_csv(output_path, index=False)
    transformations = [
        f"{JOIN_DESCRIPTIONS[business_domain]} into one analytical table "
        f"({len(analytical_table)} rows)",
        f"wrote analytical table to {output_path}",
    ]

    if database_url:
        load_to_postgres(analytical_table, "orders_analytical", database_url)
        transformations.append("loaded analytical table into postgres table 'orders_analytical'")

    return output_path, transformations


def load_to_postgres(df: pd.DataFrame, table_name: str, database_url: str) -> None:
    """Loads a DataFrame into a Postgres table, replacing it if it already exists."""
    engine = sqlalchemy.create_engine(database_url)
    df.to_sql(table_name, engine, if_exists="replace", index=False)
```

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest agents/data_engineering_agent/tests/test_etl.py -v -k "not postgres and not load_to_postgres"`
Expected: PASS (non-Postgres tests: 4 existing e-commerce + 1 write test + 5 new banking tests)

(Postgres-dependent tests require a live DB per the project's existing setup — run the full file with `pytest agents/data_engineering_agent/tests/test_etl.py -v` only if Postgres is running, same as today.)

- [x] **Step 5: Commit**

```bash
git add agents/data_engineering_agent/etl.py agents/data_engineering_agent/tests/test_etl.py
git commit -m "etl.py: per-domain analytical table, add banking transaction-level join"
```

---

### Task 5: `data_engineering_agent/agent.py` — wire `business_domain` through

**Files:**
- Modify: `agents/data_engineering_agent/agent.py`
- Test: `agents/data_engineering_agent/tests/test_data_engineering_agent.py`

**Interfaces:**
- Consumes: `load_all_tables(dataset_dir, business_domain)` (Task 2), `clean_tables(tables, business_domain)` (Task 3), `run_etl(cleaned_tables, output_path, business_domain, database_url=None)` (Task 4).
- Produces: `DataEngineeringAgent.run(raw_dataset: RawDatasetRef) -> CleanedDataset` — signature unchanged (it already reads `business_domain` off `raw_dataset`).

- [x] **Step 1: Add a banking integration test**

Add to `agents/data_engineering_agent/tests/test_data_engineering_agent.py`:

```python
BANKING_SAMPLE_DIR = "data/sample/banking"


def test_agent_run_produces_cleaned_dataset_from_sample_banking(tmp_path):
    output_path = str(tmp_path / "banking_analytical.csv")
    agent = DataEngineeringAgent(output_path=output_path)
    raw = RawDatasetRef(
        dataset_path=BANKING_SAMPLE_DIR, dataset_name="berka_banking", business_domain="banking"
    )

    result = agent.run(raw)

    assert isinstance(result, CleanedDataset)
    assert result.dataset_path == output_path
    assert result.data_quality_report.n_rows > 0
    assert len(result.transformations_applied) > 0

    written = pd.read_csv(output_path)
    assert "trans_id" in written.columns
    assert "region" in written.columns
    assert len(written) > 0
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest agents/data_engineering_agent/tests/test_data_engineering_agent.py::test_agent_run_produces_cleaned_dataset_from_sample_banking -v`
Expected: FAIL — `load_all_tables() missing 1 required positional argument` (agent.py doesn't pass `business_domain` yet)

- [x] **Step 3: Wire `business_domain` through `DataEngineeringAgent.run`**

In `agents/data_engineering_agent/agent.py`, replace the `run` method body:

```python
    def run(self, raw_dataset: RawDatasetRef) -> CleanedDataset:
        """Runs profiling, cleaning, and ETL on the given raw dataset."""
        profiling_report = profile_dataset(raw_dataset)

        tables = load_all_tables(raw_dataset.dataset_path, raw_dataset.business_domain)
        cleaned_tables, clean_transformations = clean_tables(tables, raw_dataset.business_domain)
        output_path, etl_transformations = run_etl(
            cleaned_tables,
            self.output_path,
            raw_dataset.business_domain,
            database_url=self.database_url,
        )

        return CleanedDataset(
            dataset_path=output_path,
            data_quality_report=profiling_report,
            transformations_applied=clean_transformations + etl_transformations,
            business_domain=raw_dataset.business_domain,
        )
```

- [x] **Step 4: Run all data_engineering_agent tests to verify they pass**

Run: `pytest agents/data_engineering_agent/ -v -k "not postgres and not load_to_postgres"`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add agents/data_engineering_agent/agent.py agents/data_engineering_agent/tests/test_data_engineering_agent.py
git commit -m "data_engineering_agent: thread business_domain through profiling/cleaning/ETL, add banking integration test"
```

---

### Task 6: `kpi_definitions.py` — banking KPI definitions

**Files:**
- Modify: `agents/kpi_semantic_agent/kpi_definitions.py`
- Test: `agents/kpi_semantic_agent/tests/test_kpi_definitions.py`

**Interfaces:**
- Produces: `get_kpi_definitions("banking")` returns 5 `KPIDefinition`s with `dimensions=["region", "transaction_type"]`. KPI names: `total_transaction_volume`, `average_transaction_value`, `transaction_count`, `average_account_balance`, `loan_good_standing_rate`. Task 7 (`kpi_computation.py`) must return exactly these 5 names from `_compute_banking_kpis`.

- [x] **Step 1: Add the banking KPI definitions test**

Add to `agents/kpi_semantic_agent/tests/test_kpi_definitions.py`:

```python
def test_get_kpi_definitions_returns_five_banking_kpis():
    definitions = get_kpi_definitions("banking")
    assert all(isinstance(d, KPIDefinition) for d in definitions)
    names = {d.name for d in definitions}
    assert names == {
        "total_transaction_volume",
        "average_transaction_value",
        "transaction_count",
        "average_account_balance",
        "loan_good_standing_rate",
    }
    assert all(d.dimensions == ["region", "transaction_type"] for d in definitions)
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest agents/kpi_semantic_agent/tests/test_kpi_definitions.py::test_get_kpi_definitions_returns_five_banking_kpis -v`
Expected: FAIL — `KeyError: 'banking'`

- [x] **Step 3: Add the banking KPI definitions**

In `agents/kpi_semantic_agent/kpi_definitions.py`, add after `_ECOMMERCE_KPIS`:

```python
_BANKING_BREAKDOWN_DIMENSIONS = ["region", "transaction_type"]

_BANKING_KPIS = [
    KPIDefinition(
        name="total_transaction_volume",
        formula="sum(amount) where type == 'PRIJEM'",
        description="Total value of credit transactions.",
        dimensions=_BANKING_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="average_transaction_value",
        formula="total_transaction_volume / count(distinct trans_id where type == 'PRIJEM')",
        description="Average value of a credit transaction.",
        dimensions=_BANKING_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="transaction_count",
        formula="count(distinct trans_id)",
        description="Total number of transactions, both credits and debits.",
        dimensions=_BANKING_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="average_account_balance",
        formula="mean(balance)",
        description="Average account balance across all transactions.",
        dimensions=_BANKING_BREAKDOWN_DIMENSIONS,
    ),
    KPIDefinition(
        name="loan_good_standing_rate",
        formula="count(loan_status in ('A','C')) / count(loan_status is not null)",
        description="Share of loans that are in good standing (finished without issue, or running normally).",
        dimensions=_BANKING_BREAKDOWN_DIMENSIONS,
    ),
]
```

Update `_KPIS_BY_DOMAIN`:

```python
_KPIS_BY_DOMAIN = {
    "e-commerce": _ECOMMERCE_KPIS,
    "banking": _BANKING_KPIS,
}
```

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest agents/kpi_semantic_agent/tests/test_kpi_definitions.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add agents/kpi_semantic_agent/kpi_definitions.py agents/kpi_semantic_agent/tests/test_kpi_definitions.py
git commit -m "kpi_definitions.py: add 5 banking KPI definitions"
```

---

### Task 7: `kpi_computation.py` — per-domain KPI math

**Files:**
- Modify: `agents/kpi_semantic_agent/kpi_computation.py`
- Test: `agents/kpi_semantic_agent/tests/test_kpi_computation.py`

**Interfaces:**
- Consumes: banking analytical columns from Task 4 (`trans_id`, `type`, `amount`, `balance`, `loan_status`).
- Produces: `compute_kpis(df: pd.DataFrame, business_domain: str) -> dict[str, Any]` and `compute_kpi_breakdowns(df: pd.DataFrame, dimension_column: str, business_domain: str) -> dict[str, dict[str, Any]]` (both signatures changed — `business_domain` added). `_compute_banking_kpis` returns exactly the 5 keys defined in Task 6.

- [x] **Step 1: Update existing KPI computation tests, add banking tests**

In `agents/kpi_semantic_agent/tests/test_kpi_computation.py`, add `"e-commerce"` as the second argument to every `compute_kpis(df)` call (5 occurrences) and every `compute_kpi_breakdowns(df, "customer_state")` call (2 occurrences, becoming `compute_kpi_breakdowns(df, "customer_state", "e-commerce")`).

Add at the end of the file:

```python
def _banking_df(**overrides):
    base = pd.DataFrame(
        {
            "trans_id": [1, 2, 3, 4],
            "type": ["PRIJEM", "PRIJEM", "VYDAJ", "VYDAJ"],
            "amount": [500.0, 300.0, 100.0, 50.0],
            "balance": [1000.0, 1300.0, 1200.0, 1150.0],
            "loan_status": ["C", "C", "C", "C"],
        }
    )
    return base.assign(**overrides) if overrides else base


def test_compute_kpis_banking_total_transaction_volume_sums_credits_only():
    computed = compute_kpis(_banking_df(), "banking")
    assert computed["total_transaction_volume"] == 800.0


def test_compute_kpis_banking_transaction_count_counts_all_transaction_types():
    computed = compute_kpis(_banking_df(), "banking")
    assert computed["transaction_count"] == 4


def test_compute_kpis_banking_average_transaction_value_divides_volume_by_credit_count():
    computed = compute_kpis(_banking_df(), "banking")
    assert computed["average_transaction_value"] == 400.0


def test_compute_kpis_banking_average_account_balance_means_balance_column():
    computed = compute_kpis(_banking_df(), "banking")
    assert computed["average_account_balance"] == 1162.5


def test_compute_kpis_banking_loan_good_standing_rate_counts_a_and_c_as_good():
    df = _banking_df(loan_status=["A", "B", "C", "D"])
    computed = compute_kpis(df, "banking")
    assert computed["loan_good_standing_rate"] == 0.5


def test_compute_kpis_banking_loan_good_standing_rate_is_none_when_no_loan():
    df = _banking_df(loan_status=[None, None, None, None])
    computed = compute_kpis(df, "banking")
    assert computed["loan_good_standing_rate"] is None


def test_compute_kpi_breakdowns_banking_groups_by_region():
    df = _banking_df(region=["Prague", "Prague", "Brno", "Brno"])
    breakdowns = compute_kpi_breakdowns(df, "region", "banking")
    assert set(breakdowns) == {"Prague", "Brno"}
    assert breakdowns["Prague"]["total_transaction_volume"] == 500.0
```

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest agents/kpi_semantic_agent/tests/test_kpi_computation.py -v`
Expected: FAIL — `compute_kpis() missing 1 required positional argument: 'business_domain'`

- [x] **Step 3: Implement per-domain KPI computation**

Replace the full contents of `agents/kpi_semantic_agent/kpi_computation.py`:

```python
"""Computes KPI values from the analytical table, per business domain."""

from typing import Any

import pandas as pd


def compute_kpi_breakdowns(
    df: pd.DataFrame, dimension_column: str, business_domain: str
) -> dict[str, dict[str, Any]]:
    """Computes every KPI's value per distinct value of `dimension_column`.

    Applies the same formulas as `compute_kpis` to each group's subset of
    rows.
    """
    return {
        str(value): compute_kpis(group, business_domain)
        for value, group in df.dropna(subset=[dimension_column]).groupby(dimension_column)
    }


def compute_kpis(df: pd.DataFrame, business_domain: str) -> dict[str, Any]:
    """Computes the KPI values for business_domain from the analytical table."""
    if business_domain == "e-commerce":
        return _compute_ecommerce_kpis(df)
    if business_domain == "banking":
        return _compute_banking_kpis(df)
    raise KeyError(business_domain)


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

    return {
        "total_revenue": total_revenue,
        "order_count": order_count,
        "average_order_value": average_order_value,
        "average_review_score": average_review_score,
        "on_time_delivery_rate": on_time_delivery_rate,
    }


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

    return {
        "total_transaction_volume": total_transaction_volume,
        "average_transaction_value": average_transaction_value,
        "transaction_count": transaction_count,
        "average_account_balance": average_account_balance,
        "loan_good_standing_rate": loan_good_standing_rate,
    }
```

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest agents/kpi_semantic_agent/tests/test_kpi_computation.py -v`
Expected: PASS (7 existing + 7 new tests)

- [x] **Step 5: Commit**

```bash
git add agents/kpi_semantic_agent/kpi_computation.py agents/kpi_semantic_agent/tests/test_kpi_computation.py
git commit -m "kpi_computation.py: per-domain KPI math, add banking KPI computation"
```

---

### Task 8: `kpi_semantic_agent/agent.py` — wire `business_domain` through

**Files:**
- Modify: `agents/kpi_semantic_agent/agent.py`
- Test: `agents/kpi_semantic_agent/tests/test_kpi_semantic_agent.py`

**Interfaces:**
- Consumes: `get_kpi_definitions(business_domain)` (Task 6), `compute_kpis(df, business_domain)` / `compute_kpi_breakdowns(df, column, business_domain)` (Task 7).
- Produces: `KPISemanticAgent.run(cleaned: CleanedDataset) -> KPICatalog` — signature unchanged.

Note: banking's KPI math (Task 7) does no date comparisons, so banking needs no `parse_dates` columns at all.

- [x] **Step 1: Fix the stale "banking raises KeyError" test, add a real banking integration test**

`test_kpi_semantic_agent.py` currently has a test proving `business_domain` is read from `CleanedDataset` (not defaulted) by asserting `business_domain="banking"` raises `KeyError` — that assumption breaks once banking KPIs exist. In `agents/kpi_semantic_agent/tests/test_kpi_semantic_agent.py`, replace:

```python
def test_agent_run_uses_business_domain_from_cleaned_dataset_not_a_constructor_default():
    """KPISemanticAgent must read business_domain off CleanedDataset -- there's
    no constructor override, since CleanedDataset now carries it through
    from RawDatasetRef.
    """
    cleaned = CleanedDataset(
        dataset_path="data/sample/olist/does_not_matter.csv",
        data_quality_report=ProfilingReport(
            n_rows=0, n_columns=0, column_types={}, missing_values={}, duplicate_rows=0, anomalies=[]
        ),
        transformations_applied=[],
        business_domain="banking",
    )
    with pytest.raises(KeyError):
        # "banking" has no KPI definitions yet -- this proves business_domain
        # was actually read from `cleaned`, not defaulted to "e-commerce".
        KPISemanticAgent().run(cleaned)
```

with:

```python
def test_agent_run_uses_business_domain_from_cleaned_dataset_not_a_constructor_default():
    """KPISemanticAgent must read business_domain off CleanedDataset -- there's
    no constructor override, since CleanedDataset now carries it through
    from RawDatasetRef.
    """
    cleaned = CleanedDataset(
        dataset_path="data/sample/olist/does_not_matter.csv",
        data_quality_report=ProfilingReport(
            n_rows=0, n_columns=0, column_types={}, missing_values={}, duplicate_rows=0, anomalies=[]
        ),
        transformations_applied=[],
        business_domain="retail",
    )
    with pytest.raises(KeyError):
        # "retail" has no KPI definitions -- this proves business_domain was
        # actually read from `cleaned`, not defaulted to "e-commerce".
        KPISemanticAgent().run(cleaned)
```

Add at the end of the file:

```python
BANKING_SAMPLE_DIR = "data/sample/banking"


def test_agent_run_computes_banking_kpi_catalog_from_cleaned_dataset(tmp_path):
    analytical_path = str(tmp_path / "banking_analytical.csv")
    raw = RawDatasetRef(
        dataset_path=BANKING_SAMPLE_DIR, dataset_name="berka_banking", business_domain="banking"
    )
    cleaned = DataEngineeringAgent(output_path=analytical_path).run(raw)

    agent = KPISemanticAgent()
    result = agent.run(cleaned)

    assert isinstance(result, KPICatalog)
    assert {kpi.name for kpi in result.kpis} == {
        "total_transaction_volume",
        "average_transaction_value",
        "transaction_count",
        "average_account_balance",
        "loan_good_standing_rate",
    }
    assert result.computed_values["transaction_count"] > 0

    assert set(result.breakdowns) == {"region", "transaction_type"}
    assert len(result.breakdowns["transaction_type"]) > 0
```

- [x] **Step 2: Run tests to verify the new one fails**

Run: `pytest agents/kpi_semantic_agent/tests/test_kpi_semantic_agent.py::test_agent_run_computes_banking_kpi_catalog_from_cleaned_dataset -v`
Expected: FAIL — `KeyError: 'banking'` inside `kpi_semantic_agent/agent.py` (not yet updated)

- [x] **Step 3: Wire per-domain date/dimension columns through the agent**

Replace the full contents of `agents/kpi_semantic_agent/agent.py`:

```python
"""BI Semantic & KPI Agent entrypoint.

Owns KPI definitions and formulas for the business domain. Called by the
Orchestrator with a CleanedDataset and returns a KPICatalog.
"""

import pandas as pd

from agents.kpi_semantic_agent.kpi_computation import compute_kpi_breakdowns, compute_kpis
from agents.kpi_semantic_agent.kpi_definitions import get_kpi_definitions
from shared.schemas.data_contracts import CleanedDataset, KPICatalog

# Analytical-table columns that must be parsed as dates before KPI math runs,
# per business domain. Empty where no KPI needs a date comparison.
DATE_COLUMNS_BY_DOMAIN = {
    "e-commerce": ["order_delivered_customer_date", "order_estimated_delivery_date"],
    "banking": [],
}

# Breakdown dimension name (as used in KPIDefinition.dimensions) -> analytical
# table column it's computed from, per business domain.
DIMENSION_COLUMNS_BY_DOMAIN = {
    "e-commerce": {
        "category": "product_category_name_english",
        "state": "customer_state",
    },
    "banking": {
        "region": "region",
        "transaction_type": "type_label",
    },
}


class KPISemanticAgent:
    """Defines KPIs for the business domain and computes their values against the cleaned dataset."""

    def run(self, cleaned: CleanedDataset) -> KPICatalog:
        """Computes the KPI catalog for the given cleaned dataset."""
        business_domain = cleaned.business_domain
        kpi_definitions = get_kpi_definitions(business_domain)
        date_columns = DATE_COLUMNS_BY_DOMAIN[business_domain]
        dimension_columns = DIMENSION_COLUMNS_BY_DOMAIN[business_domain]

        df = pd.read_csv(cleaned.dataset_path, parse_dates=date_columns)
        computed_values = compute_kpis(df, business_domain)

        dimensions_used = {d for kpi in kpi_definitions for d in kpi.dimensions}
        breakdowns = {
            dimension: compute_kpi_breakdowns(df, column, business_domain)
            for dimension, column in dimension_columns.items()
            if dimension in dimensions_used
        }

        return KPICatalog(
            kpis=kpi_definitions, computed_values=computed_values, breakdowns=breakdowns
        )
```

- [x] **Step 4: Run all kpi_semantic_agent tests to verify they pass**

Run: `pytest agents/kpi_semantic_agent/ -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add agents/kpi_semantic_agent/agent.py agents/kpi_semantic_agent/tests/test_kpi_semantic_agent.py
git commit -m "kpi_semantic_agent: per-domain date/dimension columns, add banking integration test"
```

---

### Task 9: `trend_detection.py` — banking thresholds

**Files:**
- Modify: `agents/bi_analyst_agent/trend_detection.py`
- Test: `agents/bi_analyst_agent/tests/test_trend_detection.py`

**Interfaces:**
- No signature change — `detect_trends(kpis: KPICatalog) -> dict[str, Any]` evaluates whatever KPI names are present in `kpis.computed_values` against a single flat `THRESHOLDS` dict. Since e-commerce and banking KPI names never collide, banking thresholds are additive entries in the same dict.

- [x] **Step 1: Add banking threshold tests**

Add to `agents/bi_analyst_agent/tests/test_trend_detection.py`:

```python
def test_detect_trends_flags_loan_good_standing_rate_below_threshold_as_concerning():
    kpis = _kpi_catalog(loan_good_standing_rate=0.80)
    trends = detect_trends(kpis)
    assert trends["loan_good_standing_rate"] == {
        "value": 0.80,
        "threshold": 0.85,
        "status": "concerning",
    }


def test_detect_trends_flags_average_account_balance_at_or_above_threshold_as_healthy():
    kpis = _kpi_catalog(average_account_balance=35000.0)
    trends = detect_trends(kpis)
    assert trends["average_account_balance"] == {
        "value": 35000.0,
        "threshold": 30000.0,
        "status": "healthy",
    }
```

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest agents/bi_analyst_agent/tests/test_trend_detection.py -v`
Expected: FAIL — `KeyError: 'loan_good_standing_rate'` (`trends` dict has no such key yet)

- [x] **Step 3: Add banking thresholds**

In `agents/bi_analyst_agent/trend_detection.py`, replace `THRESHOLDS`:

```python
THRESHOLDS = {
    "on_time_delivery_rate": 0.9,
    "average_review_score": 4.0,
    "loan_good_standing_rate": 0.85,
    "average_account_balance": 30000.0,
}
```

(`detect_trends` itself needs no changes — both new keys are read from `THRESHOLDS`/`kpis.computed_values` the same way the existing two are.)

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest agents/bi_analyst_agent/tests/test_trend_detection.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add agents/bi_analyst_agent/trend_detection.py agents/bi_analyst_agent/tests/test_trend_detection.py
git commit -m "trend_detection.py: add banking KPI thresholds"
```

---

### Task 10: `monthly_trends.py` — per-domain monthly trends

**Files:**
- Modify: `agents/bi_analyst_agent/monthly_trends.py`
- Test: `agents/bi_analyst_agent/tests/test_monthly_trends.py`

**Interfaces:**
- Consumes: banking analytical columns from Task 4 (`trans_id`, `date`, `type`, `amount`, `balance`).
- Produces: `compute_monthly_trends(analytical_df: pd.DataFrame, business_domain: str) -> dict[str, Any]` (signature changed — `business_domain` added). Banking metric keys: `total_transaction_volume`, `transaction_count`, `average_account_balance` (matching Task 6/7's KPI names, so `insight_generator.py`'s `MONTHLY_TREND_LABELS` in Task 11 can key off them the same way).

- [x] **Step 1: Update existing monthly trend tests, add banking tests**

In `agents/bi_analyst_agent/tests/test_monthly_trends.py`, add `"e-commerce"` as the second argument to every `compute_monthly_trends(df)` call (6 occurrences).

Add at the end of the file:

```python
def test_compute_monthly_trends_banking_detects_increasing_transaction_volume():
    df = pd.DataFrame(
        {
            "trans_id": [1, 2, 3],
            "date": pd.to_datetime(["2018-01-05", "2018-01-10", "2018-02-05"]),
            "type": ["PRIJEM", "PRIJEM", "PRIJEM"],
            "amount": [50.0, 50.0, 150.0],
            "balance": [500.0, 550.0, 700.0],
        }
    )
    trends = compute_monthly_trends(df, "banking")
    assert trends["total_transaction_volume"] == {
        "previous_month": "2018-01",
        "latest_month": "2018-02",
        "previous_value": 100.0,
        "latest_value": 150.0,
        "pct_change": 50.0,
        "direction": "increasing",
        "series": [
            {"month": "2018-01", "value": 100.0},
            {"month": "2018-02", "value": 150.0},
        ],
    }


def test_compute_monthly_trends_banking_counts_distinct_transactions_per_month():
    df = pd.DataFrame(
        {
            "trans_id": [1, 2, 3],
            "date": pd.to_datetime(["2018-01-05", "2018-01-06", "2018-02-05"]),
            "type": ["PRIJEM", "VYDAJ", "PRIJEM"],
            "amount": [50.0, 20.0, 30.0],
            "balance": [500.0, 480.0, 510.0],
        }
    )
    trends = compute_monthly_trends(df, "banking")
    assert trends["transaction_count"]["previous_value"] == 2.0
    assert trends["transaction_count"]["latest_value"] == 1.0


def test_compute_monthly_trends_banking_averages_balance_per_month():
    df = pd.DataFrame(
        {
            "trans_id": [1, 2, 3],
            "date": pd.to_datetime(["2018-01-05", "2018-01-06", "2018-02-05"]),
            "type": ["PRIJEM", "PRIJEM", "PRIJEM"],
            "amount": [50.0, 50.0, 50.0],
            "balance": [400.0, 600.0, 900.0],
        }
    )
    trends = compute_monthly_trends(df, "banking")
    assert trends["average_account_balance"]["previous_value"] == 500.0
    assert trends["average_account_balance"]["latest_value"] == 900.0


def test_compute_monthly_trends_banking_omits_metrics_with_fewer_than_two_months():
    df = pd.DataFrame(
        {
            "trans_id": [1],
            "date": pd.to_datetime(["2018-01-05"]),
            "type": ["PRIJEM"],
            "amount": [50.0],
            "balance": [500.0],
        }
    )
    trends = compute_monthly_trends(df, "banking")
    assert trends == {}
```

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest agents/bi_analyst_agent/tests/test_monthly_trends.py -v`
Expected: FAIL — `compute_monthly_trends() missing 1 required positional argument: 'business_domain'`

- [x] **Step 3: Implement per-domain monthly trends**

Replace the full contents of `agents/bi_analyst_agent/monthly_trends.py`:

```python
"""Real month-over-month trend detection from the analytical table, per
business domain.

Unlike trend_detection.py (which only evaluates a single KPICatalog
snapshot against fixed thresholds), this buckets the underlying analytical
data by calendar month and compares the last two complete months with data.
"""

from typing import Any

import pandas as pd


def _direction(latest: float, previous: float) -> str:
    if latest > previous:
        return "increasing"
    if latest < previous:
        return "decreasing"
    return "flat"


def _trend_entry(series: pd.Series) -> dict[str, Any] | None:
    """Builds a trend entry from the last two months of a monthly series."""
    if len(series) < 2:
        return None
    previous_month, latest_month = series.index[-2], series.index[-1]
    previous_value, latest_value = float(series.iloc[-2]), float(series.iloc[-1])
    pct_change = (
        (latest_value - previous_value) / previous_value * 100 if previous_value else 0.0
    )
    return {
        "previous_month": previous_month,
        "latest_month": latest_month,
        "previous_value": previous_value,
        "latest_value": latest_value,
        "pct_change": round(pct_change, 2),
        "direction": _direction(latest_value, previous_value),
        "series": [
            {"month": month, "value": float(value)} for month, value in series.items()
        ],
    }


MIN_ORDER_COUNT_RATIO = 0.2


def _complete_months(count_by_month: pd.Series) -> pd.Index:
    """Excludes trailing months whose row count is far below typical volume
    (e.g. a handful of stray rows after the data effectively ends) --
    otherwise they get treated as "the latest month" and produce a
    misleading near-total-collapse trend.
    """
    if count_by_month.empty:
        return count_by_month.index
    threshold = count_by_month.max() * MIN_ORDER_COUNT_RATIO
    return count_by_month[count_by_month >= threshold].index


def compute_monthly_trends(analytical_df: pd.DataFrame, business_domain: str) -> dict[str, Any]:
    """Computes month-over-month trends for business_domain from the analytical table."""
    if business_domain == "e-commerce":
        return _compute_ecommerce_monthly_trends(analytical_df)
    if business_domain == "banking":
        return _compute_banking_monthly_trends(analytical_df)
    raise KeyError(business_domain)


def _compute_ecommerce_monthly_trends(analytical_df: pd.DataFrame) -> dict[str, Any]:
    """Computes month-over-month trends for revenue, order count, and review score."""
    df = analytical_df.copy()
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    df["month"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m")

    orders_level = df[["order_id", "month", "review_score"]].drop_duplicates(subset="order_id")

    non_canceled = df[df["order_status"] != "canceled"]
    revenue_by_month = non_canceled.groupby("month")["price"].sum().sort_index()
    order_count_by_month = orders_level.groupby("month")["order_id"].nunique().sort_index()
    review_score_by_month = orders_level.groupby("month")["review_score"].mean().sort_index()

    complete_months = _complete_months(order_count_by_month)
    revenue_by_month = revenue_by_month.reindex(complete_months)
    order_count_by_month = order_count_by_month.reindex(complete_months)
    review_score_by_month = review_score_by_month.reindex(complete_months)

    trends = {}
    for name, series in (
        ("total_revenue", revenue_by_month),
        ("order_count", order_count_by_month),
        ("average_review_score", review_score_by_month),
    ):
        entry = _trend_entry(series)
        if entry is not None:
            trends[name] = entry

    return trends


def _compute_banking_monthly_trends(analytical_df: pd.DataFrame) -> dict[str, Any]:
    """Computes month-over-month trends for transaction volume, count, and balance."""
    df = analytical_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["month"] = df["date"].dt.strftime("%Y-%m")

    credits = df[df["type"] == "PRIJEM"]
    volume_by_month = credits.groupby("month")["amount"].sum().sort_index()
    transaction_count_by_month = df.groupby("month")["trans_id"].nunique().sort_index()
    balance_by_month = df.groupby("month")["balance"].mean().sort_index()

    complete_months = _complete_months(transaction_count_by_month)
    volume_by_month = volume_by_month.reindex(complete_months)
    transaction_count_by_month = transaction_count_by_month.reindex(complete_months)
    balance_by_month = balance_by_month.reindex(complete_months)

    trends = {}
    for name, series in (
        ("total_transaction_volume", volume_by_month),
        ("transaction_count", transaction_count_by_month),
        ("average_account_balance", balance_by_month),
    ):
        entry = _trend_entry(series)
        if entry is not None:
            trends[name] = entry

    return trends
```

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest agents/bi_analyst_agent/tests/test_monthly_trends.py -v`
Expected: PASS (6 existing + 4 new tests)

- [x] **Step 5: Commit**

```bash
git add agents/bi_analyst_agent/monthly_trends.py agents/bi_analyst_agent/tests/test_monthly_trends.py
git commit -m "monthly_trends.py: per-domain monthly trends, add banking implementation"
```

---

### Task 11: `insight_generator.py` — banking insight labels

**Files:**
- Modify: `agents/bi_analyst_agent/insight_generator.py`
- Test: `agents/bi_analyst_agent/tests/test_insight_generator.py`, `test_insight_generator_monthly.py`

**Interfaces:**
- No signature change — `generate_insights` and `generate_monthly_trend_insights` already fall back to a generic `f"{kpi_name}: {status}"` label when a KPI name isn't in `TITLES`/`MONTHLY_TREND_LABELS`, so banking entries are purely additive.

- [x] **Step 1: Add banking label tests**

Add to `agents/bi_analyst_agent/tests/test_insight_generator.py`:

```python
def test_generate_insights_produces_named_title_for_concerning_loan_good_standing_rate():
    kpis = _kpi_catalog(loan_good_standing_rate=0.80)
    trends = {
        "loan_good_standing_rate": {"value": 0.80, "threshold": 0.85, "status": "concerning"}
    }
    insights = generate_insights(kpis, trends)
    assert insights[0].title == "Loan default rate above target"
```

Add to `agents/bi_analyst_agent/tests/test_insight_generator_monthly.py`:

```python
def test_generate_monthly_trend_insights_uses_named_label_for_transaction_volume():
    monthly_trends = {
        "total_transaction_volume": {
            "previous_month": "2018-01",
            "latest_month": "2018-02",
            "previous_value": 100.0,
            "latest_value": 150.0,
            "pct_change": 50.0,
            "direction": "increasing",
        }
    }
    insights = generate_monthly_trend_insights(monthly_trends)
    assert insights[0].title == "Transaction volume increasing month-over-month"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `pytest agents/bi_analyst_agent/tests/test_insight_generator.py agents/bi_analyst_agent/tests/test_insight_generator_monthly.py -v`
Expected: FAIL — titles fall back to the generic `"loan_good_standing_rate: concerning"` / `"total_transaction_volume increasing month-over-month"` form instead of the named ones asserted above.

- [x] **Step 3: Add banking entries to the label dicts**

In `agents/bi_analyst_agent/insight_generator.py`, update `TITLES`:

```python
TITLES = {
    ("on_time_delivery_rate", "healthy"): "Strong on-time delivery",
    ("on_time_delivery_rate", "concerning"): "On-time delivery rate below target",
    ("average_review_score", "healthy"): "Strong customer satisfaction",
    ("average_review_score", "concerning"): "Review scores below target",
    ("loan_good_standing_rate", "healthy"): "Strong loan repayment performance",
    ("loan_good_standing_rate", "concerning"): "Loan default rate above target",
    ("average_account_balance", "healthy"): "Healthy average account balance",
    ("average_account_balance", "concerning"): "Average account balance below target",
}
```

Update `MONTHLY_TREND_LABELS`:

```python
MONTHLY_TREND_LABELS = {
    "total_revenue": "Revenue",
    "order_count": "Order volume",
    "average_review_score": "Review score",
    "total_transaction_volume": "Transaction volume",
    "transaction_count": "Transaction count",
    "average_account_balance": "Account balance",
}
```

- [x] **Step 4: Run tests to verify they pass**

Run: `pytest agents/bi_analyst_agent/tests/test_insight_generator.py agents/bi_analyst_agent/tests/test_insight_generator_monthly.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add agents/bi_analyst_agent/insight_generator.py agents/bi_analyst_agent/tests/test_insight_generator.py agents/bi_analyst_agent/tests/test_insight_generator_monthly.py
git commit -m "insight_generator.py: add banking insight titles and trend labels"
```

---

### Task 12: `bi_analyst_agent/agent.py` — wire `business_domain` through

**Files:**
- Modify: `agents/bi_analyst_agent/agent.py`
- Test: `agents/bi_analyst_agent/tests/test_bi_analyst_agent.py`

**Interfaces:**
- Consumes: `compute_monthly_trends(analytical_df, business_domain)` (Task 10).
- Produces: `BIAnalystAgent.run(cleaned: CleanedDataset, kpis: KPICatalog) -> AnalysisResult` — signature unchanged.

- [x] **Step 1: Add a banking integration test**

Add to `agents/bi_analyst_agent/tests/test_bi_analyst_agent.py`:

```python
BANKING_SAMPLE_DIR = "data/sample/banking"


def test_agent_run_produces_analysis_result_from_real_banking_kpi_catalog(tmp_path):
    analytical_path = str(tmp_path / "banking_analytical.csv")
    raw = RawDatasetRef(
        dataset_path=BANKING_SAMPLE_DIR, dataset_name="berka_banking", business_domain="banking"
    )
    cleaned = DataEngineeringAgent(output_path=analytical_path).run(raw)
    kpis = KPISemanticAgent().run(cleaned)

    result = BIAnalystAgent().run(cleaned, kpis)

    assert isinstance(result, AnalysisResult)
    assert result.trends["loan_good_standing_rate"] == {
        "value": kpis.computed_values["loan_good_standing_rate"],
        "threshold": 0.85,
        "status": "healthy"
        if kpis.computed_values["loan_good_standing_rate"] >= 0.85
        else "concerning",
    }
    assert "monthly" in result.trends
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest agents/bi_analyst_agent/tests/test_bi_analyst_agent.py::test_agent_run_produces_analysis_result_from_real_banking_kpi_catalog -v`
Expected: FAIL — `compute_monthly_trends() missing 1 required positional argument: 'business_domain'`

- [x] **Step 3: Pass `business_domain` through**

In `agents/bi_analyst_agent/agent.py`, change the `run` method's `compute_monthly_trends` call:

```python
        analytical_df = pd.read_csv(cleaned.dataset_path)
        monthly_trends = compute_monthly_trends(analytical_df, cleaned.business_domain)
```

- [x] **Step 4: Run all bi_analyst_agent tests to verify they pass**

Run: `pytest agents/bi_analyst_agent/ -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
git add agents/bi_analyst_agent/agent.py agents/bi_analyst_agent/tests/test_bi_analyst_agent.py
git commit -m "bi_analyst_agent: pass business_domain to monthly trend computation, add banking integration test"
```

---

### Task 13: End-to-end banking pipeline test + docs

**Files:**
- Modify: `tests/test_end_to_end.py`
- Modify: `README.md`, `agents/kpi_semantic_agent/README.md`, `agents/data_engineering_agent/README.md`, `agents/bi_analyst_agent/README.md`

**Interfaces:**
- Consumes: every module changed in Tasks 2-12, wired together via `BIFlowOrchestrator.run_pipeline` (unchanged — already domain-agnostic).

- [x] **Step 1: Add the end-to-end banking test**

Add to `tests/test_end_to_end.py`:

```python
def test_full_pipeline_runs_end_to_end_on_banking_sample_data(tmp_path):
    orchestrator = BIFlowOrchestrator(
        analytical_path=str(tmp_path / "banking_analytical.csv"),
        dashboard_layout_path=str(tmp_path / "banking_dashboard_layout.json"),
    )
    raw = RawDatasetRef(
        dataset_path="data/sample/banking",
        dataset_name="berka_banking",
        business_domain="banking",
    )

    result = orchestrator.run_pipeline(raw)

    assert isinstance(result, AuditReport)
    assert result.validation_status in ("passed", "passed_with_warnings")
    assert len(result.traceability_log) == 4
    assert "total_transaction_volume" in result.explanations
```

- [x] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_end_to_end.py::test_full_pipeline_runs_end_to_end_on_banking_sample_data -v`
Expected: FAIL only if any earlier task's change was missed — if Tasks 1-12 are complete, this should already pass on the first run (nothing left to implement in this task; it's a full-pipeline confirmation, not a new code path).

- [x] **Step 3: If it fails, diagnose against the specific task that owns the broken module; if it passes, proceed**

Run: `pytest tests/test_end_to_end.py -v`
Expected: PASS (both e-commerce and banking end-to-end tests)

- [x] **Step 4: Run the full test suite**

Run: `pytest -v -k "not postgres and not load_to_postgres"`
Expected: PASS across every agent, orchestrator, and shared schema test.

- [x] **Step 5: Update documentation**

In `README.md`, update the `## Other useful commands` section to add a banking example:

```markdown
- `python -m orchestrator data/sample/banking banking --no-postgres` — run
  the pipeline against the banking domain (Berka dataset sample)
```

In `agents/kpi_semantic_agent/README.md`, `agents/data_engineering_agent/README.md`, and `agents/bi_analyst_agent/README.md`, add a short note (in whatever "status"/"next steps" section each already has) that the agent now supports both `"e-commerce"` and `"banking"` business domains, linking to [docs/superpowers/specs/2026-09-16-multi-domain-banking-design.md](../../docs/superpowers/specs/2026-09-16-multi-domain-banking-design.md) for the design rationale.

- [x] **Step 6: Commit**

```bash
git add tests/test_end_to_end.py README.md agents/kpi_semantic_agent/README.md agents/data_engineering_agent/README.md agents/bi_analyst_agent/README.md
git commit -m "Add end-to-end banking pipeline test, document multi-domain support"
```

---

## Manual verification (after Task 13)

Run the full pipeline against the banking sample through the actual CLI and dashboard, mirroring how the e-commerce domain is verified in the README:

```bash
python -m orchestrator data/sample/banking banking --no-postgres
```

Then start the API and frontend (`uvicorn agents.dashboard_agent.api:create_app --factory` and `cd frontend && npm run dev`) and confirm `http://localhost:3000` renders the 5 banking KPI cards, region/transaction-type breakdowns, and monthly trend chart with real numbers — proving the "zero frontend changes" claim in the spec holds in practice, not just in the code review.

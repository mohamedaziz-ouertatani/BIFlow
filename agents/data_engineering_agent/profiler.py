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
    "telco": {
        "customers": "customers.csv",
    },
}

CSV_SEP_BY_DOMAIN = {
    "e-commerce": ",",
    "banking": ";",
    "telco": ",",
}

# "bank"/"account" on trans are counterparty bank codes only present on
# inter-bank transfers — mostly empty, otherwise a string code, which
# pandas can't infer a single dtype for from chunked reads (DtypeWarning).
DTYPE_OVERRIDES_BY_TABLE = {
    "trans": {"bank": "string", "account": "string"},
}


# Loads every raw table for the given business domain from disk.
def load_all_tables(dataset_dir: str, business_domain: str) -> dict[str, pd.DataFrame]:
    """Loads every table for business_domain from dataset_dir, keyed by logical table name."""
    filenames = TABLE_FILENAMES_BY_DOMAIN[business_domain]
    sep = CSV_SEP_BY_DOMAIN[business_domain]
    return {
        logical_name: pd.read_csv(
            os.path.join(dataset_dir, filename),
            sep=sep,
            dtype=DTYPE_OVERRIDES_BY_TABLE.get(logical_name),
        )
        for logical_name, filename in filenames.items()
    }


# Profiles a single table: row/column counts, types, missing values, duplicates, anomalies.
def profile_table(name: str, df: pd.DataFrame) -> dict[str, Any]:
    """Profiles a single table: row/column counts, types, missing values, duplicates, anomalies."""
    n_rows = len(df)
    n_columns = len(df.columns)
    column_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
    missing_values = (
        {col: ratio for col, ratio in (df.isna().sum() / n_rows).items()} if n_rows else {}
    )
    duplicate_rows = int(df.duplicated().sum())

    anomalies = []
    if duplicate_rows:
        anomalies.append(f"{duplicate_rows} duplicate rows")
    for col, ratio in missing_values.items():
        if ratio > 0.5:
            anomalies.append(f"column '{col}' has {ratio * 100:.1f}% missing values")

    return {
        "n_rows": n_rows,
        "n_columns": n_columns,
        "column_types": column_types,
        "missing_values": missing_values,
        "duplicate_rows": duplicate_rows,
        "anomalies": anomalies,
    }


# Profiles every table in the raw dataset and aggregates results into one ProfilingReport.
def profile_dataset(raw_dataset: RawDatasetRef) -> ProfilingReport:
    """Profiles every table in raw_dataset.dataset_path and aggregates into one ProfilingReport."""
    tables = load_all_tables(raw_dataset.dataset_path, raw_dataset.business_domain)

    n_rows = 0
    n_columns = 0
    column_types: dict[str, str] = {}
    missing_values: dict[str, float] = {}
    duplicate_rows = 0
    anomalies: list[str] = []

    for table_name, df in tables.items():
        report = profile_table(table_name, df)
        n_rows += report["n_rows"]
        n_columns += report["n_columns"]
        duplicate_rows += report["duplicate_rows"]
        for col, dtype in report["column_types"].items():
            column_types[f"{table_name}.{col}"] = dtype
        for col, ratio in report["missing_values"].items():
            missing_values[f"{table_name}.{col}"] = ratio
        anomalies.extend(f"{table_name}: {a}" for a in report["anomalies"])

    return ProfilingReport(
        n_rows=n_rows,
        n_columns=n_columns,
        column_types=column_types,
        missing_values=missing_values,
        duplicate_rows=duplicate_rows,
        anomalies=anomalies,
    )

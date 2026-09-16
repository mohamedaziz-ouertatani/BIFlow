"""Tests for profiler.py: per-table profiling and dataset-level aggregation."""

import pandas as pd

from agents.data_engineering_agent.profiler import (
    load_all_tables,
    profile_dataset,
    profile_table,
)
from shared.schemas.data_contracts import ProfilingReport, RawDatasetRef

SAMPLE_DIR = "data/sample/olist"


def test_profile_table_reports_row_and_column_counts():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    report = profile_table("mytable", df)
    assert report["n_rows"] == 3
    assert report["n_columns"] == 2


def test_profile_table_reports_column_types():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    report = profile_table("mytable", df)
    assert report["column_types"] == {"a": "int64", "b": "object"}


def test_profile_table_reports_missing_value_ratios():
    df = pd.DataFrame({"a": [1, None, None, 4]})
    report = profile_table("mytable", df)
    assert report["missing_values"] == {"a": 0.5}


def test_profile_table_reports_duplicate_row_count():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    report = profile_table("mytable", df)
    assert report["duplicate_rows"] == 1


def test_profile_table_flags_duplicate_rows_as_anomaly():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    report = profile_table("mytable", df)
    assert "1 duplicate rows" in report["anomalies"]


def test_profile_table_flags_high_missing_ratio_column_as_anomaly():
    df = pd.DataFrame({"a": [1, None, None, None]})
    report = profile_table("mytable", df)
    assert "column 'a' has 75.0% missing values" in report["anomalies"]


def test_profile_table_no_anomalies_for_clean_data():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    report = profile_table("mytable", df)
    assert report["anomalies"] == []


def test_load_all_tables_loads_every_olist_table_by_logical_name():
    tables = load_all_tables(SAMPLE_DIR, "e-commerce")
    assert set(tables.keys()) == {
        "orders",
        "customers",
        "order_items",
        "order_payments",
        "order_reviews",
        "products",
        "sellers",
        "geolocation",
        "category_translation",
    }
    assert len(tables["orders"]) == 500
    assert "order_id" in tables["orders"].columns


def test_profile_dataset_aggregates_all_tables_into_one_report():
    raw = RawDatasetRef(
        dataset_path=SAMPLE_DIR, dataset_name="olist_ecommerce", business_domain="e-commerce"
    )
    report = profile_dataset(raw)

    assert isinstance(report, ProfilingReport)
    tables = load_all_tables(SAMPLE_DIR, "e-commerce")
    assert report.n_rows == sum(len(df) for df in tables.values())
    assert report.n_columns == sum(len(df.columns) for df in tables.values())
    assert "orders.order_id" in report.column_types
    assert "customers.customer_id" in report.column_types
    assert "orders.order_id" in report.missing_values


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

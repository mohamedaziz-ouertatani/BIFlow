"""Tests for cleaner.py: per-table data-quality cleaning rules."""

import pandas as pd

from agents.data_engineering_agent.cleaner import clean_tables


def test_clean_tables_drops_exact_duplicate_rows():
    tables = {
        "sellers": pd.DataFrame({"seller_id": ["a", "a", "b"], "seller_city": ["x", "x", "y"]})
    }
    cleaned, _ = clean_tables(tables)
    assert len(cleaned["sellers"]) == 2


def test_clean_tables_parses_timestamp_columns_in_orders():
    tables = {
        "orders": pd.DataFrame(
            {
                "order_id": ["o1"],
                "order_purchase_timestamp": ["2018-01-01 10:00:00"],
                "order_delivered_customer_date": ["2018-01-10 10:00:00"],
            }
        )
    }
    cleaned, _ = clean_tables(tables)
    assert pd.api.types.is_datetime64_any_dtype(cleaned["orders"]["order_purchase_timestamp"])
    assert pd.api.types.is_datetime64_any_dtype(
        cleaned["orders"]["order_delivered_customer_date"]
    )


def test_clean_tables_drops_order_items_with_null_or_negative_price():
    tables = {
        "order_items": pd.DataFrame(
            {
                "order_id": ["o1", "o2", "o3"],
                "price": [10.0, None, -5.0],
            }
        )
    }
    cleaned, transformations = clean_tables(tables)
    assert list(cleaned["order_items"]["order_id"]) == ["o1"]
    assert any("dropped 2 order_items rows with null/negative price" in t for t in transformations)


def test_clean_tables_fills_missing_product_category_with_unknown():
    tables = {
        "products": pd.DataFrame(
            {"product_id": ["p1", "p2"], "product_category_name": ["toys", None]}
        )
    }
    cleaned, transformations = clean_tables(tables)
    assert list(cleaned["products"]["product_category_name"]) == ["toys", "unknown"]
    assert any("filled missing product_category_name with 'unknown'" in t for t in transformations)

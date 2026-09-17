"""Tests for cleaner.py: per-table data-quality cleaning rules."""

import pandas as pd

from agents.data_engineering_agent.cleaner import clean_tables


def test_clean_tables_drops_exact_duplicate_rows():
    tables = {
        "sellers": pd.DataFrame({"seller_id": ["a", "a", "b"], "seller_city": ["x", "x", "y"]})
    }
    cleaned, _ = clean_tables(tables, "e-commerce")
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
    cleaned, _ = clean_tables(tables, "e-commerce")
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
    cleaned, transformations = clean_tables(tables, "e-commerce")
    assert list(cleaned["order_items"]["order_id"]) == ["o1"]
    assert any("dropped 2 order_items rows with null/negative price" in t for t in transformations)


def test_clean_tables_fills_missing_product_category_with_unknown():
    tables = {
        "products": pd.DataFrame(
            {"product_id": ["p1", "p2"], "product_category_name": ["toys", None]}
        )
    }
    cleaned, transformations = clean_tables(tables, "e-commerce")
    assert list(cleaned["products"]["product_category_name"]) == ["toys", "unknown"]
    assert any("filled missing product_category_name with 'unknown'" in t for t in transformations)


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


def test_clean_tables_fills_blank_total_charges_with_zero():
    tables = {
        "customers": pd.DataFrame(
            {
                "customerID": ["c1", "c2"],
                "tenure": [0, 34],
                "TotalCharges": [" ", "1889.5"],
            }
        )
    }
    cleaned, transformations = clean_tables(tables, "telco")
    assert list(cleaned["customers"]["TotalCharges"]) == [0.0, 1889.5]
    assert any("filled 1 blank TotalCharges values with 0" in t for t in transformations)


def test_clean_tables_leaves_telco_total_charges_untouched_when_no_blanks():
    tables = {
        "customers": pd.DataFrame(
            {"customerID": ["c1"], "tenure": [5], "TotalCharges": ["100.0"]}
        )
    }
    cleaned, transformations = clean_tables(tables, "telco")
    assert list(cleaned["customers"]["TotalCharges"]) == [100.0]
    assert not any("TotalCharges" in t for t in transformations)

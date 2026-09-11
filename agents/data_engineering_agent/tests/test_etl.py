"""Tests for etl.py: joining cleaned tables into one order-item-level analytical table."""

import pandas as pd
import sqlalchemy

from agents.data_engineering_agent.etl import build_analytical_table, load_to_postgres, run_etl

TEST_DATABASE_URL = "postgresql://biflow:biflow@localhost:5433/biflow"


def test_build_analytical_table_joins_order_items_with_orders_and_customers():
    tables = {
        "order_items": pd.DataFrame(
            {"order_id": ["o1"], "order_item_id": [1], "product_id": ["p1"], "seller_id": ["s1"], "price": [100.0]}
        ),
        "orders": pd.DataFrame({"order_id": ["o1"], "customer_id": ["c1"], "order_status": ["delivered"]}),
        "customers": pd.DataFrame({"customer_id": ["c1"], "customer_state": ["SP"]}),
        "order_payments": pd.DataFrame(columns=["order_id", "payment_value", "payment_type", "payment_installments"]),
        "order_reviews": pd.DataFrame(columns=["order_id", "review_score", "review_creation_date"]),
        "products": pd.DataFrame({"product_id": ["p1"], "product_category_name": ["toys"]}),
        "sellers": pd.DataFrame({"seller_id": ["s1"], "seller_state": ["RJ"]}),
        "category_translation": pd.DataFrame(
            {"product_category_name": ["toys"], "product_category_name_english": ["toys_en"]}
        ),
    }
    result = build_analytical_table(tables)
    assert len(result) == 1
    row = result.iloc[0]
    assert row["order_id"] == "o1"
    assert row["customer_state"] == "SP"
    assert row["order_status"] == "delivered"


def test_build_analytical_table_sums_payment_value_per_order():
    tables = {
        "order_items": pd.DataFrame(
            {"order_id": ["o1"], "order_item_id": [1], "product_id": ["p1"], "seller_id": ["s1"], "price": [100.0]}
        ),
        "orders": pd.DataFrame({"order_id": ["o1"], "customer_id": ["c1"], "order_status": ["delivered"]}),
        "customers": pd.DataFrame({"customer_id": ["c1"], "customer_state": ["SP"]}),
        "order_payments": pd.DataFrame(
            {
                "order_id": ["o1", "o1"],
                "payment_value": [60.0, 40.0],
                "payment_type": ["credit_card", "voucher"],
                "payment_installments": [2, 1],
            }
        ),
        "order_reviews": pd.DataFrame(columns=["order_id", "review_score", "review_creation_date"]),
        "products": pd.DataFrame({"product_id": ["p1"], "product_category_name": ["toys"]}),
        "sellers": pd.DataFrame({"seller_id": ["s1"], "seller_state": ["RJ"]}),
        "category_translation": pd.DataFrame(
            {"product_category_name": ["toys"], "product_category_name_english": ["toys_en"]}
        ),
    }
    result = build_analytical_table(tables)
    assert result.iloc[0]["total_payment_value"] == 100.0


def test_build_analytical_table_uses_latest_review_score_per_order():
    tables = {
        "order_items": pd.DataFrame(
            {"order_id": ["o1"], "order_item_id": [1], "product_id": ["p1"], "seller_id": ["s1"], "price": [100.0]}
        ),
        "orders": pd.DataFrame({"order_id": ["o1"], "customer_id": ["c1"], "order_status": ["delivered"]}),
        "customers": pd.DataFrame({"customer_id": ["c1"], "customer_state": ["SP"]}),
        "order_payments": pd.DataFrame(columns=["order_id", "payment_value", "payment_type", "payment_installments"]),
        "order_reviews": pd.DataFrame(
            {
                "order_id": ["o1", "o1"],
                "review_score": [2, 5],
                "review_creation_date": ["2018-01-01 00:00:00", "2018-01-05 00:00:00"],
            }
        ),
        "products": pd.DataFrame({"product_id": ["p1"], "product_category_name": ["toys"]}),
        "sellers": pd.DataFrame({"seller_id": ["s1"], "seller_state": ["RJ"]}),
        "category_translation": pd.DataFrame(
            {"product_category_name": ["toys"], "product_category_name_english": ["toys_en"]}
        ),
    }
    result = build_analytical_table(tables)
    assert result.iloc[0]["review_score"] == 5


def test_build_analytical_table_joins_english_category_name_and_seller_state():
    tables = {
        "order_items": pd.DataFrame(
            {"order_id": ["o1"], "order_item_id": [1], "product_id": ["p1"], "seller_id": ["s1"], "price": [100.0]}
        ),
        "orders": pd.DataFrame({"order_id": ["o1"], "customer_id": ["c1"], "order_status": ["delivered"]}),
        "customers": pd.DataFrame({"customer_id": ["c1"], "customer_state": ["SP"]}),
        "order_payments": pd.DataFrame(columns=["order_id", "payment_value", "payment_type", "payment_installments"]),
        "order_reviews": pd.DataFrame(columns=["order_id", "review_score", "review_creation_date"]),
        "products": pd.DataFrame({"product_id": ["p1"], "product_category_name": ["brinquedos"]}),
        "sellers": pd.DataFrame({"seller_id": ["s1"], "seller_state": ["RJ"]}),
        "category_translation": pd.DataFrame(
            {"product_category_name": ["brinquedos"], "product_category_name_english": ["toys"]}
        ),
    }
    result = build_analytical_table(tables)
    row = result.iloc[0]
    assert row["product_category_name_english"] == "toys"
    assert row["seller_state"] == "RJ"


def test_run_etl_writes_analytical_table_to_output_path(tmp_path):
    tables = {
        "order_items": pd.DataFrame(
            {"order_id": ["o1"], "order_item_id": [1], "product_id": ["p1"], "seller_id": ["s1"], "price": [100.0]}
        ),
        "orders": pd.DataFrame({"order_id": ["o1"], "customer_id": ["c1"], "order_status": ["delivered"]}),
        "customers": pd.DataFrame({"customer_id": ["c1"], "customer_state": ["SP"]}),
        "order_payments": pd.DataFrame(columns=["order_id", "payment_value", "payment_type", "payment_installments"]),
        "order_reviews": pd.DataFrame(columns=["order_id", "review_score", "review_creation_date"]),
        "products": pd.DataFrame({"product_id": ["p1"], "product_category_name": ["toys"]}),
        "sellers": pd.DataFrame({"seller_id": ["s1"], "seller_state": ["RJ"]}),
        "category_translation": pd.DataFrame(
            {"product_category_name": ["toys"], "product_category_name_english": ["toys_en"]}
        ),
    }
    output_path = str(tmp_path / "analytical.csv")

    written_path, transformations = run_etl(tables, output_path)

    assert written_path == output_path
    written = pd.read_csv(output_path)
    assert len(written) == 1
    assert any("wrote" in t and output_path in t for t in transformations)


def test_run_etl_loads_into_postgres_when_database_url_given(tmp_path):
    tables = {
        "order_items": pd.DataFrame(
            {"order_id": ["o1"], "order_item_id": [1], "product_id": ["p1"], "seller_id": ["s1"], "price": [42.0]}
        ),
        "orders": pd.DataFrame({"order_id": ["o1"], "customer_id": ["c1"], "order_status": ["delivered"]}),
        "customers": pd.DataFrame({"customer_id": ["c1"], "customer_state": ["SP"]}),
        "order_payments": pd.DataFrame(columns=["order_id", "payment_value", "payment_type", "payment_installments"]),
        "order_reviews": pd.DataFrame(columns=["order_id", "review_score", "review_creation_date"]),
        "products": pd.DataFrame({"product_id": ["p1"], "product_category_name": ["toys"]}),
        "sellers": pd.DataFrame({"seller_id": ["s1"], "seller_state": ["RJ"]}),
        "category_translation": pd.DataFrame(
            {"product_category_name": ["toys"], "product_category_name_english": ["toys_en"]}
        ),
    }
    output_path = str(tmp_path / "analytical.csv")

    _, transformations = run_etl(tables, output_path, database_url=TEST_DATABASE_URL)

    assert any("postgres" in t.lower() for t in transformations)
    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        rows = conn.execute(
            sqlalchemy.text("SELECT order_id, price FROM orders_analytical")
        ).fetchall()
    assert [tuple(r) for r in rows] == [("o1", 42.0)]


def test_load_to_postgres_writes_dataframe_rows_into_named_table():
    df = pd.DataFrame({"order_id": ["o1", "o2"], "price": [10.0, 20.0]})
    table_name = "test_orders_analytical_load"

    load_to_postgres(df, table_name, TEST_DATABASE_URL)

    engine = sqlalchemy.create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        rows = conn.execute(
            sqlalchemy.text(f"SELECT order_id, price FROM {table_name} ORDER BY order_id")
        ).fetchall()
    assert [tuple(r) for r in rows] == [("o1", 10.0), ("o2", 20.0)]

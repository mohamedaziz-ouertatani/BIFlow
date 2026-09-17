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
    result = build_analytical_table(tables, "e-commerce")
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
    result = build_analytical_table(tables, "e-commerce")
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
    result = build_analytical_table(tables, "e-commerce")
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
    result = build_analytical_table(tables, "e-commerce")
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

    written_path, transformations = run_etl(tables, output_path, "e-commerce")

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

    _, transformations = run_etl(tables, output_path, "e-commerce", database_url=TEST_DATABASE_URL)

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


def _telco_tables():
    return {
        "customers": pd.DataFrame(
            {
                "customerID": ["c1", "c2"],
                "gender": ["Female", "Male"],
                "SeniorCitizen": [0, 1],
                "Contract": ["Month-to-month", "Two year"],
                "InternetService": ["DSL", "Fiber optic"],
                "MonthlyCharges": [29.85, 89.1],
                "TotalCharges": [29.85, 1889.5],
                "Churn": ["No", "Yes"],
            }
        )
    }


def test_build_analytical_table_renames_telco_columns_to_snake_case():
    result = build_analytical_table(_telco_tables(), "telco")
    assert len(result) == 2
    assert set(result.columns) >= {
        "customer_id",
        "senior_citizen",
        "contract",
        "internet_service",
        "monthly_charges",
        "total_charges",
        "churn",
    }
    assert "customerID" not in result.columns


def test_run_etl_writes_telco_analytical_table_to_output_path(tmp_path):
    output_path = str(tmp_path / "telco_analytical.csv")
    written_path, transformations = run_etl(_telco_tables(), output_path, "telco")
    assert written_path == output_path
    written = pd.read_csv(output_path)
    assert len(written) == 2
    assert "customer_id" in written.columns

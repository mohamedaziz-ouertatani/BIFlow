"""ETL logic for the Data Engineering Agent: builds one analytical table per
business domain by joining that domain's cleaned tables together."""

import os

import pandas as pd
import sqlalchemy

TYPE_LABELS = {"PRIJEM": "credit", "VYDAJ": "debit"}

JOIN_DESCRIPTIONS = {
    "e-commerce": "joined order_items/orders/customers/payments/reviews/products/sellers",
    "banking": "joined trans/account/district/loan",
    "telco": "renamed customers columns to snake_case (already one row per customer)",
}

# customers.csv ships PascalCase/camelCase headers; every other domain's
# analytical table uses snake_case, so rename for consistency.
TELCO_COLUMN_RENAMES = {
    "customerID": "customer_id",
    "gender": "gender",
    "SeniorCitizen": "senior_citizen",
    "Partner": "partner",
    "Dependents": "dependents",
    "tenure": "tenure",
    "PhoneService": "phone_service",
    "MultipleLines": "multiple_lines",
    "InternetService": "internet_service",
    "OnlineSecurity": "online_security",
    "OnlineBackup": "online_backup",
    "DeviceProtection": "device_protection",
    "TechSupport": "tech_support",
    "StreamingTV": "streaming_tv",
    "StreamingMovies": "streaming_movies",
    "Contract": "contract",
    "PaperlessBilling": "paperless_billing",
    "PaymentMethod": "payment_method",
    "MonthlyCharges": "monthly_charges",
    "TotalCharges": "total_charges",
    "Churn": "churn",
}


# Dispatches to the domain-specific table join.
def build_analytical_table(tables: dict[str, pd.DataFrame], business_domain: str) -> pd.DataFrame:
    """Joins cleaned tables into one analytical table for business_domain."""
    if business_domain == "e-commerce":
        return _build_ecommerce_table(tables)
    if business_domain == "banking":
        return _build_banking_table(tables)
    if business_domain == "telco":
        return _build_telco_table(tables)
    raise KeyError(business_domain)


# Joins cleaned Olist tables into one order-item-level analytical table.
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


# Joins cleaned Berka tables into one transaction-level analytical table.
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


# Renames the single customers table to snake_case; no joins needed (one row per customer).
def _build_telco_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Renames the single customers table to snake_case columns.

    Grain: one row per customer -- already the analytical-table grain, so
    unlike the other two domains there's nothing to join.
    """
    return tables["customers"].rename(columns=TELCO_COLUMN_RENAMES)


# Builds the analytical table, writes it as CSV, and optionally loads it into Postgres.
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


# Writes a DataFrame into a Postgres table, replacing it if it already exists.
def load_to_postgres(df: pd.DataFrame, table_name: str, database_url: str) -> None:
    """Loads a DataFrame into a Postgres table, replacing it if it already exists."""
    engine = sqlalchemy.create_engine(database_url)
    df.to_sql(table_name, engine, if_exists="replace", index=False)

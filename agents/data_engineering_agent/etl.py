"""ETL logic for the Data Engineering Agent: builds one order-item-level
analytical table by joining the cleaned Olist tables together."""

import os

import pandas as pd
import sqlalchemy


def build_analytical_table(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Joins cleaned tables into one order-item-level analytical table.

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


def run_etl(
    cleaned_tables: dict[str, pd.DataFrame], output_path: str, database_url: str | None = None
) -> tuple[str, list[str]]:
    """Builds the analytical table and writes it to output_path as CSV.

    If database_url is given, also loads the analytical table into a
    Postgres table (`orders_analytical`) — the CSV remains the interchange
    format between agents; Postgres is an additional persistence sink.

    Returns the output path and a list of human-readable transformations applied.
    """
    analytical_table = build_analytical_table(cleaned_tables)
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    analytical_table.to_csv(output_path, index=False)
    transformations = [
        f"joined order_items/orders/customers/payments/reviews/products/sellers "
        f"into one analytical table ({len(analytical_table)} rows)",
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

"""Data cleaning/quality logic for the Data Engineering Agent."""

import pandas as pd


def clean_tables(tables: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], list[str]]:
    """Applies data-quality cleaning rules to every table.

    Returns the cleaned tables plus a list of human-readable transformations applied.
    """
    cleaned: dict[str, pd.DataFrame] = {}
    transformations: list[str] = []

    for name, df in tables.items():
        before = len(df)
        df = df.drop_duplicates()
        dropped = before - len(df)
        if dropped:
            transformations.append(f"{name}: dropped {dropped} exact duplicate rows")

        date_cols = [c for c in df.columns if "timestamp" in c or c.endswith("_date")]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col])
        if date_cols:
            transformations.append(f"{name}: parsed {date_cols} as datetime")

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

        cleaned[name] = df

    return cleaned, transformations

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

        date_cols = [
            c for c in df.columns if "timestamp" in c or c.endswith(("_date", "_at"))
        ]
        for col in date_cols:
            df[col] = pd.to_datetime(df[col])
        if date_cols:
            transformations.append(f"{name}: parsed {date_cols} as datetime")

        if business_domain == "e-commerce":
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

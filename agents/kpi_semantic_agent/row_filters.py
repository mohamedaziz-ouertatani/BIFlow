"""Row-level filters behind each KPI's value.

kpi_computation.py's aggregate functions and the dashboard API's
/api/drilldown endpoint both need "which rows count for this KPI" -- this
module is the single definition of that, so the two can't silently drift
apart if a KPI's filter ever changes.
"""

from typing import Callable

import pandas as pd

_RowFilter = Callable[[pd.DataFrame], pd.DataFrame]

_ECOMMERCE_FILTERS: dict[str, _RowFilter] = {
    "total_revenue": lambda df: df[df["order_status"] != "canceled"],
    "average_order_value": lambda df: df[df["order_status"] != "canceled"],
    "order_count": lambda df: df,
    "average_review_score": lambda df: df[df["review_score"].notna()],
    "on_time_delivery_rate": lambda df: df[df["order_delivered_customer_date"].notna()],
}

_BANKING_FILTERS: dict[str, _RowFilter] = {
    "total_transaction_volume": lambda df: df[df["type"] == "PRIJEM"],
    "average_transaction_value": lambda df: df[df["type"] == "PRIJEM"],
    "transaction_count": lambda df: df,
    "average_account_balance": lambda df: df[df["balance"].notna()],
    "loan_good_standing_rate": lambda df: df[df["loan_status"].notna()],
}

_TELCO_FILTERS: dict[str, _RowFilter] = {
    "churn_rate": lambda df: df,
    "average_monthly_charges": lambda df: df,
    "average_tenure_months": lambda df: df,
    "total_customers": lambda df: df,
}

_FILTERS_BY_DOMAIN: dict[str, dict[str, _RowFilter]] = {
    "e-commerce": _ECOMMERCE_FILTERS,
    "banking": _BANKING_FILTERS,
    "telco": _TELCO_FILTERS,
}

# The date column each domain's monthly trends bucket by (see
# bi_analyst_agent/monthly_trends.py), for month-scoped drill-downs. None
# where the domain has no time dimension (telco).
DATE_COLUMN_BY_DOMAIN: dict[str, str | None] = {
    "e-commerce": "order_purchase_timestamp",
    "banking": "date",
    "telco": None,
}


# Returns the analytical-table rows behind a KPI's value, optionally scoped to one month.
def filter_rows(
    df: pd.DataFrame, business_domain: str, kpi_name: str, month: str | None = None
) -> pd.DataFrame:
    """Returns the rows that back `kpi_name`'s value for `business_domain`.

    Raises KeyError for an unknown business_domain or kpi_name.
    """
    matching = _FILTERS_BY_DOMAIN[business_domain][kpi_name](df)

    date_column = DATE_COLUMN_BY_DOMAIN[business_domain]
    if month and date_column:
        dates = pd.to_datetime(matching[date_column])
        matching = matching[dates.dt.strftime("%Y-%m") == month]

    return matching

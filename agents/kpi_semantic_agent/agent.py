"""BI Semantic & KPI Agent entrypoint.

Owns KPI definitions and formulas for the business domain. Called by the
Orchestrator with a CleanedDataset and returns a KPICatalog.
"""

import pandas as pd

from agents.kpi_semantic_agent.kpi_computation import compute_kpi_breakdowns, compute_kpis
from agents.kpi_semantic_agent.kpi_definitions import get_kpi_definitions
from shared.schemas.data_contracts import CleanedDataset, KPICatalog

# Analytical-table columns that must be parsed as dates before KPI math runs,
# per business domain. Empty where no KPI needs a date comparison.
DATE_COLUMNS_BY_DOMAIN = {
    "e-commerce": ["order_delivered_customer_date", "order_estimated_delivery_date"],
    "banking": [],
    "telco": [],
}

# Breakdown dimension name (as used in KPIDefinition.dimensions) -> analytical
# table column it's computed from, per business domain.
DIMENSION_COLUMNS_BY_DOMAIN = {
    "e-commerce": {
        "category": "product_category_name_english",
        "state": "customer_state",
    },
    "banking": {
        "region": "region",
    },
    "telco": {
        "contract": "contract",
        "internet_service": "internet_service",
    },
}


class KPISemanticAgent:
    """Defines KPIs for the business domain and computes their values against the cleaned dataset."""

    # Computes the KPI catalog for the given cleaned dataset.
    def run(self, cleaned: CleanedDataset) -> KPICatalog:
        """Computes the KPI catalog for the given cleaned dataset."""
        business_domain = cleaned.business_domain
        kpi_definitions = get_kpi_definitions(business_domain)
        date_columns = DATE_COLUMNS_BY_DOMAIN[business_domain]

        # The analytical table was saved as CSV, so dates come back as plain text: parse the columns the
        # KPI math compares. low_memory=False reads the file in one pass so column types are inferred
        # consistently (avoids mixed-type warnings).
        df = pd.read_csv(cleaned.dataset_path, parse_dates=date_columns, low_memory=False)
        computed_values = compute_kpis(df, business_domain)

        # Only compute breakdowns for dimensions that at least one KPI actually declares.
        dimensions_used = {d for kpi in kpi_definitions for d in kpi.dimensions}
        dimension_columns = DIMENSION_COLUMNS_BY_DOMAIN[business_domain]
        breakdowns = {
            dimension: compute_kpi_breakdowns(df, column, business_domain)
            for dimension, column in dimension_columns.items()
            if dimension in dimensions_used
        }

        return KPICatalog(
            kpis=kpi_definitions,
            computed_values=computed_values,
            breakdowns=breakdowns,
            business_domain=business_domain,
        )

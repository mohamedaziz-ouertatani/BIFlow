"""BI Semantic & KPI Agent entrypoint.

Owns KPI definitions and formulas for the business domain. Called by the
Orchestrator with a CleanedDataset and returns a KPICatalog.
"""

import pandas as pd

from agents.kpi_semantic_agent.kpi_computation import compute_kpis
from agents.kpi_semantic_agent.kpi_definitions import get_kpi_definitions
from shared.schemas.data_contracts import CleanedDataset, KPICatalog

# Analytical-table columns that must be parsed as dates before KPI math runs,
# per business domain. Empty where no KPI needs a date comparison.
DATE_COLUMNS_BY_DOMAIN = {
    "e-commerce": ["order_delivered_customer_date", "order_estimated_delivery_date"],
    "banking": [],
}


class KPISemanticAgent:
    """Defines KPIs for the business domain and computes their values against the cleaned dataset."""

    def run(self, cleaned: CleanedDataset) -> KPICatalog:
        """Computes the KPI catalog for the given cleaned dataset."""
        business_domain = cleaned.business_domain
        kpi_definitions = get_kpi_definitions(business_domain)
        date_columns = DATE_COLUMNS_BY_DOMAIN[business_domain]

        df = pd.read_csv(cleaned.dataset_path, parse_dates=date_columns)
        computed_values = compute_kpis(df, business_domain)

        return KPICatalog(kpis=kpi_definitions, computed_values=computed_values)

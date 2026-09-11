"""BI Semantic & KPI Agent entrypoint.

Owns KPI definitions and formulas for the business domain. Called by the
Orchestrator with a CleanedDataset and returns a KPICatalog.
"""

import pandas as pd

from agents.kpi_semantic_agent.kpi_computation import compute_kpis
from agents.kpi_semantic_agent.kpi_definitions import get_kpi_definitions
from shared.schemas.data_contracts import CleanedDataset, KPICatalog

DATE_COLUMNS = ["order_delivered_customer_date", "order_estimated_delivery_date"]


class KPISemanticAgent:
    """Defines KPIs for the business domain and computes their values against the cleaned dataset."""

    def run(self, cleaned: CleanedDataset) -> KPICatalog:
        """Computes the KPI catalog for the given cleaned dataset."""
        kpi_definitions = get_kpi_definitions(cleaned.business_domain)

        df = pd.read_csv(cleaned.dataset_path, parse_dates=DATE_COLUMNS)
        computed_values = compute_kpis(df)

        return KPICatalog(kpis=kpi_definitions, computed_values=computed_values)

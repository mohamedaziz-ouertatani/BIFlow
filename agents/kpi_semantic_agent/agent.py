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

    def __init__(self, business_domain: str = "e-commerce") -> None:
        # TODO (owner): CleanedDataset doesn't carry business_domain today —
        # thread it through the shared contract once multiple domains exist.
        self.business_domain = business_domain

    def run(self, cleaned: CleanedDataset) -> KPICatalog:
        """Computes the KPI catalog for the given cleaned dataset."""
        df = pd.read_csv(cleaned.dataset_path, parse_dates=DATE_COLUMNS)

        kpi_definitions = get_kpi_definitions(self.business_domain)
        computed_values = compute_kpis(df)

        return KPICatalog(kpis=kpi_definitions, computed_values=computed_values)

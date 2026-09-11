"""BI Semantic & KPI Agent entrypoint.

Owns KPI definitions and formulas for the business domain. Called by the
Orchestrator with a CleanedDataset and returns a KPICatalog.
"""

from agents.kpi_semantic_agent.kpi_definitions import get_kpi_definitions
from shared.schemas.data_contracts import CleanedDataset, KPICatalog


class KPISemanticAgent:
    """
    Defines KPIs for the business domain and computes their values against
    the cleaned dataset.

    TODO (owner): implement domain-specific KPI definitions (see
    kpi_definitions.py) and the computation logic that produces
    KPICatalog.computed_values.
    """

    def run(self, cleaned: CleanedDataset) -> KPICatalog:
        """Computes the KPI catalog for the given cleaned dataset.

        TODO (owner): implement — load KPI definitions, compute their values
        against cleaned.dataset_path, and assemble the KPICatalog.
        """
        raise NotImplementedError("TODO: implement KPI/Semantic Agent pipeline")

"""KPI definitions for the business domain(s) BIFlow supports."""

from shared.schemas.data_contracts import KPIDefinition


def get_kpi_definitions(business_domain: str) -> list[KPIDefinition]:
    """Returns the list of KPI definitions relevant to the given business domain.

    TODO (owner): implement — define KPIs per domain (e.g. "e-commerce":
    revenue, AOV, churn rate; "banking": NPL ratio, CAC, etc.) and document
    them in docs/kpi_catalog.md.
    """
    raise NotImplementedError("TODO: implement KPI definitions")

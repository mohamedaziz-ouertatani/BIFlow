"""Tests for kpi_definitions.py: KPI definitions per business domain."""

from agents.kpi_semantic_agent.kpi_definitions import get_kpi_definitions
from shared.schemas.data_contracts import KPIDefinition


def test_get_kpi_definitions_returns_five_ecommerce_kpis():
    definitions = get_kpi_definitions("e-commerce")
    assert all(isinstance(d, KPIDefinition) for d in definitions)
    names = {d.name for d in definitions}
    assert names == {
        "total_revenue",
        "average_order_value",
        "order_count",
        "average_review_score",
        "on_time_delivery_rate",
    }

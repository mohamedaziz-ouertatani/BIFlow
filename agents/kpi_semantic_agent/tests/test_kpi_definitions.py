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
    assert all(d.dimensions == ["category", "state"] for d in definitions)


def test_get_kpi_definitions_returns_five_banking_kpis():
    definitions = get_kpi_definitions("banking")
    assert all(isinstance(d, KPIDefinition) for d in definitions)
    by_name = {d.name: d for d in definitions}
    assert set(by_name) == {
        "total_transaction_volume",
        "average_transaction_value",
        "transaction_count",
        "average_account_balance",
        "loan_good_standing_rate",
    }
    assert by_name["loan_good_standing_rate"].dimensions == []
    assert all(
        d.dimensions == ["region"] for name, d in by_name.items() if name != "loan_good_standing_rate"
    )


def test_get_kpi_definitions_returns_four_telco_kpis():
    definitions = get_kpi_definitions("telco")
    assert all(isinstance(d, KPIDefinition) for d in definitions)
    names = {d.name for d in definitions}
    assert names == {
        "churn_rate",
        "average_monthly_charges",
        "average_tenure_months",
        "total_customers",
    }
    assert all(d.dimensions == ["contract", "internet_service"] for d in definitions)

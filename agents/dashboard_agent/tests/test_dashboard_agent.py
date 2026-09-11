"""Tests for the Dashboard Generator Agent."""

import json

from agents.dashboard_agent.agent import DashboardAgent
from shared.schemas.data_contracts import (
    AnalysisResult,
    DashboardSpec,
    Insight,
    KPICatalog,
    KPIDefinition,
)


def test_agent_run_writes_layout_and_returns_dashboard_spec(tmp_path):
    layout_path = str(tmp_path / "dashboard_layout.json")
    agent = DashboardAgent(layout_path=layout_path)

    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="total_revenue", formula="sum(price)", description="Total revenue", dimensions=[]
            )
        ],
        computed_values={"total_revenue": 123.45},
    )
    analysis = AnalysisResult(
        insights=[
            Insight(
                title="Revenue dip",
                description="Dropped 20%",
                related_kpi="total_revenue",
                severity="warning",
            )
        ],
        trends={},
    )

    result = agent.run(analysis, kpis)

    assert isinstance(result, DashboardSpec)
    assert result.kpis_shown == ["total_revenue"]
    assert "kpi_cards" in result.visualizations
    assert "insights_panel" in result.visualizations

    with open(layout_path) as f:
        written_layout = json.load(f)
    assert written_layout["kpi_cards"][0]["name"] == "total_revenue"
    assert written_layout["insights"][0]["title"] == "Revenue dip"

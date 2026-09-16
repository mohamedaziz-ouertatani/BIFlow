"""Tests for the Dashboard Generator Agent."""

import json

from agents.dashboard_agent.agent import DashboardAgent
from shared.schemas.data_contracts import (
    AnalysisResult,
    AuditReport,
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


def test_attach_audit_report_adds_explanation_to_each_kpi_card(tmp_path):
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
    analysis = AnalysisResult(insights=[], trends={})
    agent.run(analysis, kpis)

    audit = AuditReport(
        validation_status="passed",
        explanations={"total_revenue": "total_revenue = sum(price) = 123.45"},
        traceability_log=[],
    )
    agent.attach_audit_report(audit)

    with open(layout_path) as f:
        written_layout = json.load(f)
    assert written_layout["kpi_cards"][0]["explanation"] == "total_revenue = sum(price) = 123.45"


def test_attach_audit_report_leaves_explanation_null_when_missing(tmp_path):
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
    agent.run(AnalysisResult(insights=[], trends={}), kpis)

    agent.attach_audit_report(
        AuditReport(validation_status="passed", explanations={}, traceability_log=[])
    )

    with open(layout_path) as f:
        written_layout = json.load(f)
    assert written_layout["kpi_cards"][0]["explanation"] is None

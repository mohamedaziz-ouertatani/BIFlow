"""Tests for layout_builder.py: building a JSON-serializable dashboard layout."""

from agents.dashboard_agent.layout_builder import build_layout
from shared.schemas.data_contracts import AnalysisResult, Insight, KPICatalog, KPIDefinition


def test_build_layout_includes_a_kpi_card_per_kpi():
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="total_revenue", formula="sum(price)", description="Total revenue", dimensions=[]
            )
        ],
        computed_values={"total_revenue": 123.45},
    )
    analysis = AnalysisResult(insights=[], trends={})

    layout = build_layout(analysis, kpis)

    assert layout["kpi_cards"] == [
        {"name": "total_revenue", "label": "Total revenue", "value": 123.45}
    ]


def test_build_layout_includes_an_insight_entry_per_insight():
    kpis = KPICatalog(kpis=[], computed_values={})
    analysis = AnalysisResult(
        insights=[
            Insight(
                title="Revenue dip in March",
                description="Revenue dropped 20% vs February",
                related_kpi="total_revenue",
                severity="warning",
            )
        ],
        trends={},
    )

    layout = build_layout(analysis, kpis)

    assert layout["insights"] == [
        {
            "title": "Revenue dip in March",
            "description": "Revenue dropped 20% vs February",
            "severity": "warning",
        }
    ]

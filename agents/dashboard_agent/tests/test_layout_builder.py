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
        {
            "name": "total_revenue",
            "label": "Total revenue",
            "value": 123.45,
            "comparison": None,
        }
    ]


def test_build_layout_includes_monthly_comparison_on_the_matching_kpi_card():
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="total_revenue", formula="sum(price)", description="Total revenue", dimensions=[]
            )
        ],
        computed_values={"total_revenue": 150.0},
    )
    analysis = AnalysisResult(
        insights=[],
        trends={
            "monthly": {
                "total_revenue": {
                    "previous_month": "2018-01",
                    "latest_month": "2018-02",
                    "previous_value": 100.0,
                    "latest_value": 150.0,
                    "pct_change": 50.0,
                    "direction": "increasing",
                    "series": [
                        {"month": "2018-01", "value": 100.0},
                        {"month": "2018-02", "value": 150.0},
                    ],
                }
            }
        },
    )

    layout = build_layout(analysis, kpis)

    assert layout["kpi_cards"][0]["comparison"] == {
        "previous_month": "2018-01",
        "latest_month": "2018-02",
        "previous_value": 100.0,
        "latest_value": 150.0,
        "pct_change": 50.0,
        "direction": "increasing",
    }


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
            "related_kpi": "total_revenue",
            "severity": "warning",
        }
    ]


def test_build_layout_includes_monthly_trend_series_for_charting():
    kpis = KPICatalog(kpis=[], computed_values={})
    analysis = AnalysisResult(
        insights=[],
        trends={
            "on_time_delivery_rate": {"value": 0.9, "threshold": 0.9, "status": "healthy"},
            "monthly": {
                "total_revenue": {
                    "previous_month": "2018-01",
                    "latest_month": "2018-02",
                    "previous_value": 100.0,
                    "latest_value": 150.0,
                    "pct_change": 50.0,
                    "direction": "increasing",
                    "series": [
                        {"month": "2018-01", "value": 100.0},
                        {"month": "2018-02", "value": 150.0},
                    ],
                }
            },
        },
    )

    layout = build_layout(analysis, kpis)

    assert layout["monthly_trends"] == {
        "total_revenue": [
            {"month": "2018-01", "value": 100.0},
            {"month": "2018-02", "value": 150.0},
        ]
    }


def test_build_layout_returns_empty_monthly_trends_when_none_present():
    kpis = KPICatalog(kpis=[], computed_values={})
    analysis = AnalysisResult(insights=[], trends={})

    layout = build_layout(analysis, kpis)

    assert layout["monthly_trends"] == {}

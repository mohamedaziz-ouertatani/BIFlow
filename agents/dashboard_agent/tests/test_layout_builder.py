"""Tests for layout_builder.py: building a JSON-serializable dashboard layout."""

from agents.dashboard_agent.layout_builder import build_layout
from agents.kpi_semantic_agent.kpi_definitions import get_kpi_definitions
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
            "month": None,
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


def test_build_layout_includes_a_category_breakdown_per_dimensioned_kpi():
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="total_revenue",
                formula="sum(price)",
                description="Total revenue",
                dimensions=["category"],
            )
        ],
        computed_values={"total_revenue": 300.0},
        breakdowns={
            "category": {
                "electronics": {"total_revenue": 200.0},
                "books": {"total_revenue": 100.0},
            }
        },
    )
    analysis = AnalysisResult(insights=[], trends={})

    layout = build_layout(analysis, kpis)

    assert layout["category_breakdowns"] == {
        "total_revenue_by_category": [
            {"label": "electronics", "value": 200.0},
            {"label": "books", "value": 100.0},
        ]
    }


def test_build_layout_caps_category_breakdowns_at_eight_items_with_an_other_bucket():
    groups = {f"cat{i}": {"total_revenue": float(10 - i)} for i in range(10)}
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="total_revenue",
                formula="sum(price)",
                description="Total revenue",
                dimensions=["category"],
                additive=True,
            )
        ],
        computed_values={"total_revenue": 55.0},
        breakdowns={"category": groups},
    )
    analysis = AnalysisResult(insights=[], trends={})

    layout = build_layout(analysis, kpis)

    points = layout["category_breakdowns"]["total_revenue_by_category"]
    assert len(points) == 8
    assert points[-1]["label"] == "Other"
    assert points[-1]["value"] == sum(10 - i for i in range(7, 10))


def test_build_layout_truncates_a_non_additive_kpi_to_the_top_items_without_an_other_bucket():
    # Summing averages or rates into "Other" is meaningless (an "Other" review
    # score of 255 on a 1-5 scale), so non-additive KPIs are cut off instead.
    groups = {f"cat{i}": {"average_review_score": 5.0 - i * 0.1} for i in range(10)}
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="average_review_score",
                formula="mean(review_score)",
                description="Average review score",
                dimensions=["category"],
            )
        ],
        computed_values={"average_review_score": 4.5},
        breakdowns={"category": groups},
    )
    analysis = AnalysisResult(insights=[], trends={})

    layout = build_layout(analysis, kpis)

    points = layout["category_breakdowns"]["average_review_score_by_category"]
    assert [p["label"] for p in points] == [f"cat{i}" for i in range(8)]
    assert all(p["label"] != "Other" for p in points)
    assert all(1 <= p["value"] <= 5 for p in points)


def test_build_layout_omits_a_dimension_kpi_pair_with_no_breakdown_data():
    kpis = KPICatalog(
        kpis=[
            KPIDefinition(
                name="total_revenue",
                formula="sum(price)",
                description="Total revenue",
                dimensions=["category"],
            )
        ],
        computed_values={"total_revenue": 0.0},
        breakdowns={},
    )
    analysis = AnalysisResult(insights=[], trends={})

    layout = build_layout(analysis, kpis)

    assert layout["category_breakdowns"] == {}


def test_build_layout_includes_a_region_breakdown_for_every_banking_kpi():
    definitions = get_kpi_definitions("banking")
    kpis = KPICatalog(
        kpis=definitions,
        computed_values={d.name: 1.0 for d in definitions},
        breakdowns={
            "region": {
                "Prague": {d.name: 2.0 for d in definitions},
                "north Moravia": {d.name: 1.0 for d in definitions},
            }
        },
        business_domain="banking",
    )

    layout = build_layout(AnalysisResult(insights=[], trends={}), kpis)

    assert set(layout["category_breakdowns"]) == {f"{d.name}_by_region" for d in definitions}
    assert "loan_good_standing_rate_by_region" in layout["category_breakdowns"]

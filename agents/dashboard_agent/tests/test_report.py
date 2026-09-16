"""Tests for report.py: PDF snapshot generation from the dashboard layout."""

from agents.dashboard_agent.report import build_pdf


def test_build_pdf_starts_with_pdf_magic_bytes():
    layout = {"kpi_cards": [], "insights": [], "monthly_trends": {}}
    pdf_bytes = build_pdf(layout)
    assert pdf_bytes.startswith(b"%PDF")


def test_build_pdf_includes_kpi_label_and_value():
    layout = {
        "kpi_cards": [{"name": "total_revenue", "label": "Total revenue", "value": 68048.73}],
        "insights": [],
        "monthly_trends": {},
    }
    pdf_bytes = build_pdf(layout)
    assert b"Total revenue" in pdf_bytes
    assert b"68048.73" in pdf_bytes


def test_build_pdf_includes_insight_title_and_description():
    layout = {
        "kpi_cards": [],
        "insights": [
            {
                "title": "Revenue up",
                "description": "Grew 10%",
                "related_kpi": "total_revenue",
                "severity": "info",
            }
        ],
        "monthly_trends": {},
    }
    pdf_bytes = build_pdf(layout)
    assert b"Revenue up" in pdf_bytes
    assert b"Grew 10%" in pdf_bytes


def test_build_pdf_includes_business_domain_when_present():
    layout = {"business_domain": "banking", "kpi_cards": [], "insights": [], "monthly_trends": {}}
    pdf_bytes = build_pdf(layout)
    assert b"banking" in pdf_bytes


def test_build_pdf_includes_comparison_direction_when_present():
    layout = {
        "kpi_cards": [
            {
                "name": "total_revenue",
                "label": "Total revenue",
                "value": 150.0,
                "comparison": {
                    "previous_month": "2018-01",
                    "latest_month": "2018-02",
                    "previous_value": 100.0,
                    "latest_value": 150.0,
                    "pct_change": 50.0,
                    "direction": "increasing",
                },
            }
        ],
        "insights": [],
        "monthly_trends": {},
    }
    pdf_bytes = build_pdf(layout)
    assert b"increasing" in pdf_bytes

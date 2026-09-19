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


def test_build_pdf_lists_findings_before_kpis_sorted_by_severity():
    layout = {
        "kpi_cards": [],
        "monthly_trends": {},
        "insights": [
            {"title": "Minor note", "description": "d", "related_kpi": "", "severity": "info"},
            {"title": "Big problem", "description": "d", "related_kpi": "", "severity": "critical"},
            {"title": "Watch this", "description": "d", "related_kpi": "", "severity": "warning"},
        ],
    }
    pdf_bytes = build_pdf(layout)
    assert b"Findings" in pdf_bytes
    assert b"1 critical" in pdf_bytes
    assert (
        pdf_bytes.index(b"Big problem")
        < pdf_bytes.index(b"Watch this")
        < pdf_bytes.index(b"Minor note")
    )


def test_build_pdf_sorts_kpis_by_attention_and_labels_findings():
    layout = {
        "kpi_cards": [
            {"name": "quiet", "label": "Quiet KPI", "value": 1},
            {"name": "hot", "label": "Hot KPI", "value": 2},
        ],
        "monthly_trends": {},
        "insights": [
            {
                "title": "Spike",
                "description": "d",
                "related_kpi": "hot",
                "severity": "critical",
                "month": "2018-02",
            }
        ],
    }
    pdf_bytes = build_pdf(layout)
    assert pdf_bytes.index(b"Hot KPI") < pdf_bytes.index(b"Quiet KPI")
    assert b"1 critical" in pdf_bytes
    assert b"No findings" in pdf_bytes
    assert b"2018-02" in pdf_bytes

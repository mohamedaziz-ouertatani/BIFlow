"""Tests for app.py: the Streamlit dashboard entrypoint, run headlessly via AppTest."""

import json
import os

from streamlit.testing.v1 import AppTest

APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app.py")


def _write_layout(tmp_path, layout):
    layout_path = str(tmp_path / "dashboard_layout.json")
    with open(layout_path, "w") as f:
        json.dump(layout, f)
    return layout_path


def test_app_renders_a_metric_per_kpi_card(tmp_path, monkeypatch):
    layout_path = _write_layout(
        tmp_path,
        {
            "kpi_cards": [{"name": "total_revenue", "label": "Total revenue", "value": 123.45}],
            "insights": [],
        },
    )
    monkeypatch.setenv("DASHBOARD_LAYOUT_PATH", layout_path)

    at = AppTest.from_file(APP_PATH)
    at.run()

    assert at.metric[0].label == "Total revenue"
    assert at.metric[0].value == "123.45"


def test_app_rounds_long_float_kpi_values_to_two_decimals(tmp_path, monkeypatch):
    layout_path = _write_layout(
        tmp_path,
        {
            "kpi_cards": [
                {
                    "name": "on_time_delivery_rate",
                    "label": "On-time delivery rate",
                    "value": 0.9385171790235082,
                }
            ],
            "insights": [],
        },
    )
    monkeypatch.setenv("DASHBOARD_LAYOUT_PATH", layout_path)

    at = AppTest.from_file(APP_PATH)
    at.run()

    assert at.metric[0].value == "0.94"


def test_app_renders_insights_by_severity(tmp_path, monkeypatch):
    layout_path = _write_layout(
        tmp_path,
        {
            "kpi_cards": [],
            "insights": [
                {"title": "Revenue dip", "description": "Dropped 20%", "severity": "warning"},
                {"title": "Great month", "description": "Up 10%", "severity": "info"},
            ],
        },
    )
    monkeypatch.setenv("DASHBOARD_LAYOUT_PATH", layout_path)

    at = AppTest.from_file(APP_PATH)
    at.run()

    assert "Revenue dip" in at.warning[0].value
    assert "Great month" in at.info[0].value


def test_app_shows_placeholder_when_no_layout_exists(tmp_path, monkeypatch):
    monkeypatch.setenv("DASHBOARD_LAYOUT_PATH", str(tmp_path / "missing.json"))

    at = AppTest.from_file(APP_PATH)
    at.run()

    assert len(at.metric) == 0
    assert "No dashboard data yet" in at.warning[0].value

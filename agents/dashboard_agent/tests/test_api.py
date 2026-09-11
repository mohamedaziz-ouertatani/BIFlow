"""Tests for api.py: the FastAPI backend serving the dashboard layout to the Next.js frontend."""

import json

from fastapi.testclient import TestClient

from agents.dashboard_agent.api import create_app


def _write_layout(tmp_path, layout):
    layout_path = str(tmp_path / "dashboard_layout.json")
    with open(layout_path, "w") as f:
        json.dump(layout, f)
    return layout_path


def test_health_endpoint_returns_ok():
    client = TestClient(create_app(layout_path="unused.json"))
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dashboard_endpoint_returns_the_layout_json(tmp_path):
    layout_path = _write_layout(
        tmp_path,
        {
            "kpi_cards": [{"name": "total_revenue", "label": "Total revenue", "value": 123.45}],
            "insights": [
                {"title": "Revenue up", "description": "Grew 10%", "severity": "info"}
            ],
        },
    )
    client = TestClient(create_app(layout_path=layout_path))

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["kpi_cards"][0]["name"] == "total_revenue"
    assert body["insights"][0]["title"] == "Revenue up"


def test_dashboard_endpoint_returns_404_when_no_layout_exists(tmp_path):
    client = TestClient(create_app(layout_path=str(tmp_path / "missing.json")))

    response = client.get("/api/dashboard")

    assert response.status_code == 404

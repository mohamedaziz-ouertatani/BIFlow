"""Tests for api.py: the FastAPI backend serving the dashboard layout to the Next.js frontend."""

import json

from fastapi.testclient import TestClient

from agents.dashboard_agent.api import create_app
from agents.dashboard_agent.nl_query import OllamaTimeoutError, OllamaUnavailableError


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


def test_dashboard_endpoint_returns_domain_specific_layout(tmp_path):
    _write_layout(
        tmp_path,
        {"kpi_cards": [{"name": "total_revenue", "label": "Total revenue", "value": 1}], "insights": []},
    )
    domain_layout_path = tmp_path / "dashboard_layout_banking.json"
    with open(domain_layout_path, "w") as f:
        json.dump(
            {
                "kpi_cards": [{"name": "avg_loan_amount", "label": "Average loan amount", "value": 999}],
                "insights": [],
                "business_domain": "banking",
            },
            f,
        )
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    response = client.get("/api/dashboard", params={"domain": "banking"})

    assert response.status_code == 200
    body = response.json()
    assert body["kpi_cards"][0]["name"] == "avg_loan_amount"
    assert body["business_domain"] == "banking"


def test_dashboard_endpoint_returns_404_for_unknown_domain(tmp_path):
    _write_layout(tmp_path, {"kpi_cards": [], "insights": []})
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    response = client.get("/api/dashboard", params={"domain": "unknown"})

    assert response.status_code == 404


def test_dashboard_endpoint_rejects_path_traversal_in_domain(tmp_path):
    # A secret file outside the layout directory that a traversal attempt would try to read.
    secret_path = tmp_path.parent / "secret.json"
    secret_path.write_text('{"leaked": true}')
    _write_layout(tmp_path, {"kpi_cards": [], "insights": []})
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    response = client.get("/api/dashboard", params={"domain": "../secret"})

    assert response.status_code == 404
    secret_path.unlink()


def test_report_endpoint_returns_pdf(tmp_path):
    layout_path = _write_layout(
        tmp_path,
        {
            "kpi_cards": [{"name": "total_revenue", "label": "Total revenue", "value": 123.45}],
            "insights": [],
            "monthly_trends": {},
        },
    )
    client = TestClient(create_app(layout_path=layout_path))

    response = client.get("/api/report.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")
    assert b"Total revenue" in response.content


def test_report_endpoint_returns_404_when_no_layout_exists(tmp_path):
    client = TestClient(create_app(layout_path=str(tmp_path / "missing.json")))

    response = client.get("/api/report.pdf")

    assert response.status_code == 404


def test_query_endpoint_returns_answer_on_success(tmp_path, monkeypatch):
    layout_path = _write_layout(
        tmp_path,
        {"kpi_cards": [], "insights": [], "monthly_trends": {}},
    )
    monkeypatch.setattr(
        "agents.dashboard_agent.api.generate_answer",
        lambda question, layout: "Revenue is healthy.",
    )
    client = TestClient(create_app(layout_path=layout_path))

    response = client.post("/api/query", json={"question": "How is revenue?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "Revenue is healthy."}


def test_query_endpoint_returns_404_when_no_layout_exists(tmp_path):
    client = TestClient(create_app(layout_path=str(tmp_path / "missing.json")))

    response = client.post("/api/query", json={"question": "How is revenue?"})

    assert response.status_code == 404


def test_query_endpoint_returns_503_when_ollama_unavailable(tmp_path, monkeypatch):
    layout_path = _write_layout(tmp_path, {"kpi_cards": [], "insights": [], "monthly_trends": {}})

    def _raise(question, layout):
        raise OllamaUnavailableError("connection refused")

    monkeypatch.setattr("agents.dashboard_agent.api.generate_answer", _raise)
    client = TestClient(create_app(layout_path=layout_path))

    response = client.post("/api/query", json={"question": "How is revenue?"})

    assert response.status_code == 503
    assert "Ollama" in response.json()["detail"]


def test_query_endpoint_returns_504_when_ollama_times_out(tmp_path, monkeypatch):
    layout_path = _write_layout(tmp_path, {"kpi_cards": [], "insights": [], "monthly_trends": {}})

    def _raise(question, layout):
        raise OllamaTimeoutError("timed out")

    monkeypatch.setattr("agents.dashboard_agent.api.generate_answer", _raise)
    client = TestClient(create_app(layout_path=layout_path))

    response = client.post("/api/query", json={"question": "How is revenue?"})

    assert response.status_code == 504

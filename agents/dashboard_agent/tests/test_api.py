"""Tests for api.py: the FastAPI backend serving the dashboard layout to the Next.js frontend."""

import json

from fastapi.testclient import TestClient

from agents.dashboard_agent.api import create_app
from agents.dashboard_agent.nl_query import OllamaTimeoutError, OllamaUnavailableError
from orchestrator.orchestrator import PipelineStageError


def _write_layout(tmp_path, layout):
    layout_path = str(tmp_path / "dashboard_layout.json")
    with open(layout_path, "w") as f:
        json.dump(layout, f)
    return layout_path


def _parse_sse_events(response_text):
    events = []
    for chunk in response_text.split("\n\n"):
        chunk = chunk.strip()
        if chunk.startswith("data: "):
            events.append(json.loads(chunk[len("data: ") :]))
    return events


class _FakeOrchestrator:
    """Stands in for BIFlowOrchestrator: emits events without touching real data."""

    STAGES = ["data_engineering", "kpi_semantic", "bi_analyst", "dashboard", "auditor"]
    last_analytical_path = None

    def __init__(self, analytical_path, dashboard_layout_path, on_event):
        _FakeOrchestrator.last_analytical_path = analytical_path
        self.on_event = on_event

    def run_pipeline(self, raw_dataset):
        for stage in self.STAGES:
            self.on_event(stage, "started", {})
            self.on_event(stage, "succeeded", {})


class _FailingFakeOrchestrator:
    """Fails partway through, like a real stage raising an exception."""

    def __init__(self, analytical_path, dashboard_layout_path, on_event):
        self.on_event = on_event

    def run_pipeline(self, raw_dataset):
        self.on_event("data_engineering", "started", {})
        self.on_event("data_engineering", "succeeded", {})
        self.on_event("kpi_semantic", "started", {})
        self.on_event("kpi_semantic", "failed", {"error": "boom"})
        raise PipelineStageError("kpi_semantic", ValueError("boom"))


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


def test_query_endpoint_rejects_empty_question(tmp_path):
    layout_path = _write_layout(tmp_path, {"kpi_cards": [], "insights": [], "monthly_trends": {}})
    client = TestClient(create_app(layout_path=layout_path))

    response = client.post("/api/query", json={"question": ""})

    assert response.status_code == 422


def test_query_endpoint_rejects_oversized_question(tmp_path):
    layout_path = _write_layout(tmp_path, {"kpi_cards": [], "insights": [], "monthly_trends": {}})
    client = TestClient(create_app(layout_path=layout_path))

    response = client.post("/api/query", json={"question": "why? " * 1000})

    assert response.status_code == 422


def test_run_pipeline_streams_a_stage_event_per_transition(tmp_path, monkeypatch):
    monkeypatch.setattr("agents.dashboard_agent.api.BIFlowOrchestrator", _FakeOrchestrator)
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    response = client.get("/api/pipeline/run", params={"domain": "banking"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse_events(response.text)
    assert events[0] == {"type": "stage_started", "stage": "data_engineering"}
    assert events[1] == {"type": "stage_succeeded", "stage": "data_engineering"}
    assert events[-1] == {"type": "pipeline_succeeded"}
    stages_seen = {e["stage"] for e in events if "stage" in e}
    assert stages_seen == set(_FakeOrchestrator.STAGES)


def test_run_pipeline_scopes_the_analytical_path_to_the_domain(tmp_path, monkeypatch):
    monkeypatch.setattr("agents.dashboard_agent.api.BIFlowOrchestrator", _FakeOrchestrator)
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    client.get("/api/pipeline/run", params={"domain": "banking"})

    assert _FakeOrchestrator.last_analytical_path.endswith("analytical_table_banking.csv")


def test_run_pipeline_streams_failure_and_stops(tmp_path, monkeypatch):
    monkeypatch.setattr("agents.dashboard_agent.api.BIFlowOrchestrator", _FailingFakeOrchestrator)
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    response = client.get("/api/pipeline/run", params={"domain": "banking"})

    events = _parse_sse_events(response.text)
    assert events[-2] == {"type": "stage_failed", "stage": "kpi_semantic", "error": "boom"}
    assert events[-1] == {
        "type": "pipeline_failed",
        "stage": "kpi_semantic",
        "error": "Pipeline halted: stage 'kpi_semantic' failed: boom",
    }
    # Never reached bi_analyst/dashboard/auditor once kpi_semantic failed.
    assert not any(e.get("stage") in {"bi_analyst", "dashboard", "auditor"} for e in events)


def test_run_pipeline_returns_404_for_unknown_domain(tmp_path):
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    response = client.get("/api/pipeline/run", params={"domain": "unknown"})

    assert response.status_code == 404


def test_run_pipeline_requires_a_domain(tmp_path):
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    response = client.get("/api/pipeline/run")

    assert response.status_code == 422

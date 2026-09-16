"""Tests for nl_query.py: local-LLM-backed Q&A over the dashboard layout."""

import httpx
import pytest

from agents.dashboard_agent.nl_query import (
    OllamaTimeoutError,
    OllamaUnavailableError,
    build_context,
    generate_answer,
)


def test_build_context_includes_kpi_label_and_value():
    layout = {
        "kpi_cards": [{"name": "total_revenue", "label": "Total revenue", "value": 68048.73}],
        "monthly_trends": {},
        "insights": [],
    }
    context = build_context(layout)
    assert "Total revenue" in context
    assert "68048.73" in context


def test_build_context_includes_comparison_direction_and_pct_change():
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
        "monthly_trends": {},
        "insights": [],
    }
    context = build_context(layout)
    assert "increasing" in context
    assert "+50.0%" in context


def test_build_context_includes_monthly_trend_series():
    layout = {
        "kpi_cards": [],
        "monthly_trends": {
            "total_revenue": [
                {"month": "2018-01", "value": 100.0},
                {"month": "2018-02", "value": 150.0},
            ]
        },
        "insights": [],
    }
    context = build_context(layout)
    assert "2018-01=100.0" in context
    assert "2018-02=150.0" in context


def test_build_context_includes_insight_title_and_severity():
    layout = {
        "kpi_cards": [],
        "monthly_trends": {},
        "insights": [
            {
                "title": "Revenue spike",
                "description": "Unusual increase",
                "related_kpi": "total_revenue",
                "severity": "critical",
            }
        ],
    }
    context = build_context(layout)
    assert "Revenue spike" in context
    assert "critical" in context


def test_build_context_includes_business_domain_when_present():
    layout = {"business_domain": "banking", "kpi_cards": [], "monthly_trends": {}, "insights": []}
    context = build_context(layout)
    assert "banking" in context


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response=None, raise_exc=None):
        self._response = response
        self._raise_exc = raise_exc
        self.last_call = None

    def post(self, url, json, timeout):
        self.last_call = {"url": url, "json": json, "timeout": timeout}
        if self._raise_exc:
            raise self._raise_exc
        return self._response


def test_generate_answer_returns_response_text_from_client():
    layout = {"kpi_cards": [], "monthly_trends": {}, "insights": []}
    client = _FakeClient(response=_FakeResponse(200, {"response": "Revenue is healthy."}))

    answer = generate_answer("How is revenue?", layout, client=client)

    assert answer == "Revenue is healthy."


def test_generate_answer_sends_question_and_context_in_prompt():
    layout = {
        "kpi_cards": [{"name": "total_revenue", "label": "Total revenue", "value": 100.0}],
        "monthly_trends": {},
        "insights": [],
    }
    client = _FakeClient(response=_FakeResponse(200, {"response": "ok"}))

    generate_answer("How is revenue?", layout, client=client)

    prompt = client.last_call["json"]["prompt"]
    assert "How is revenue?" in prompt
    assert "Total revenue" in prompt


def test_generate_answer_raises_unavailable_on_connect_error():
    layout = {"kpi_cards": [], "monthly_trends": {}, "insights": []}
    client = _FakeClient(raise_exc=httpx.ConnectError("refused"))

    with pytest.raises(OllamaUnavailableError):
        generate_answer("How is revenue?", layout, client=client)


def test_generate_answer_raises_timeout_on_timeout_exception():
    layout = {"kpi_cards": [], "monthly_trends": {}, "insights": []}
    client = _FakeClient(raise_exc=httpx.TimeoutException("timed out"))

    with pytest.raises(OllamaTimeoutError):
        generate_answer("How is revenue?", layout, client=client)


def test_generate_answer_raises_unavailable_on_non_200_status():
    layout = {"kpi_cards": [], "monthly_trends": {}, "insights": []}
    client = _FakeClient(response=_FakeResponse(500, {}))

    with pytest.raises(OllamaUnavailableError):
        generate_answer("How is revenue?", layout, client=client)

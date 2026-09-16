"""Natural-language Q&A over the dashboard layout, backed by a local Ollama model."""

import os
from typing import Any, Protocol

import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")

SYSTEM_PROMPT = (
    "You are a BI assistant answering questions about a single business's "
    "dashboard. Answer ONLY using the DATA block below -- cite the actual "
    "numbers. If the question asks about something not covered by the DATA, "
    "say \"I don't have that data.\" Be concise: 2-4 sentences."
)


class OllamaUnavailableError(Exception):
    """Raised when the local Ollama server can't be reached or returns an error."""


class OllamaTimeoutError(Exception):
    """Raised when the local Ollama server doesn't respond within the timeout."""


class _HttpResponse(Protocol):
    status_code: int

    def json(self) -> Any: ...


class _HttpClient(Protocol):
    def post(self, url: str, json: dict[str, Any], timeout: float) -> _HttpResponse: ...


# Serializes KPI cards, monthly trends, and insights from the dashboard layout into a compact prompt-ready block.
def build_context(layout: dict[str, Any]) -> str:
    """Turns the dashboard layout JSON into a compact plain-text block for the LLM prompt."""
    lines: list[str] = []

    domain = layout.get("business_domain")
    if domain:
        lines.append(f"Business domain: {domain}")

    kpi_cards = layout.get("kpi_cards", [])
    if kpi_cards:
        lines.append("KPIs:")
        for card in kpi_cards:
            line = f"- {card['label']} ({card['name']}): {card['value']}"
            comparison = card.get("comparison")
            if comparison:
                line += (
                    f" [{comparison['direction']} from {comparison['previous_value']} "
                    f"in {comparison['previous_month']} to {comparison['latest_value']} "
                    f"in {comparison['latest_month']}, {comparison['pct_change']:+.1f}%]"
                )
            lines.append(line)

    monthly_trends = layout.get("monthly_trends", {})
    if monthly_trends:
        lines.append("Monthly trends:")
        for metric, series in monthly_trends.items():
            points = ", ".join(f"{p['month']}={p['value']}" for p in series)
            lines.append(f"- {metric}: {points}")

    insights = layout.get("insights", [])
    if insights:
        lines.append("Insights:")
        for insight in insights:
            lines.append(
                f"- [{insight['severity']}] {insight['title']}: {insight['description']}"
            )

    return "\n".join(lines)


# Sends the question + dashboard context to the local Ollama model and returns its answer text.
def generate_answer(question: str, layout: dict[str, Any], client: _HttpClient | None = None) -> str:
    """Builds context from layout, calls Ollama's /api/generate, returns the answer text."""
    http_client = client or httpx
    context = build_context(layout)
    prompt = f"{SYSTEM_PROMPT}\n\nDATA:\n{context}\n\nQUESTION: {question}"

    try:
        response = http_client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=30.0,
        )
    except httpx.TimeoutException as exc:
        raise OllamaTimeoutError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise OllamaUnavailableError(str(exc)) from exc

    if response.status_code != 200:
        raise OllamaUnavailableError(f"Ollama returned {response.status_code}")

    return response.json()["response"]

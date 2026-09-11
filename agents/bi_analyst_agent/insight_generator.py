"""Insight generation logic for the BI Analyst Agent."""

from typing import Any

from shared.schemas.data_contracts import Insight, KPICatalog


def generate_insights(kpis: KPICatalog, trends: dict[str, Any]) -> list[Insight]:
    """Generates human-readable insights/recommendations from KPIs and trends.

    TODO (owner): implement — likely LLM-assisted, turning detected trends
    into Insight objects (title, description, related_kpi, severity).
    """
    raise NotImplementedError("TODO: implement insight generation")

"""Trend and anomaly detection logic for the BI Analyst Agent."""

from typing import Any

from shared.schemas.data_contracts import KPICatalog


def detect_trends(kpis: KPICatalog) -> dict[str, Any]:
    """Detects trends and anomalies across the KPI catalog's computed values.

    TODO (owner): implement — e.g. time-series trend detection, statistical
    anomaly detection (z-score, IQR), or LLM-assisted pattern spotting.
    Returns a dict suitable for AnalysisResult.trends.
    """
    raise NotImplementedError("TODO: implement trend/anomaly detection")

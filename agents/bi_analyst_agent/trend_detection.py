"""Trend and anomaly detection logic for the BI Analyst Agent.

Since the agent only receives a single KPICatalog snapshot (no history to
compare against), "trend detection" here means evaluating each KPI that has
a natural business threshold and flagging it healthy vs. concerning.
"""

from typing import Any

from shared.schemas.data_contracts import KPICatalog

# Hardcoded business targets (not learned from the data): a KPI at or above its target is
# 'healthy', below it is 'concerning'.
THRESHOLDS = {
    "on_time_delivery_rate": 0.9,
    "average_review_score": 4.0,
    "loan_good_standing_rate": 0.85,
    "average_account_balance": 30000.0,
}


# Flags each threshold-backed KPI as healthy or concerning against its fixed threshold.
def detect_trends(kpis: KPICatalog) -> dict[str, Any]:
    """Evaluates threshold-backed KPIs and flags each as healthy or concerning."""
    trends = {}
    for name, threshold in THRESHOLDS.items():
        if name not in kpis.computed_values:
            continue
        value = kpis.computed_values[name]
        trends[name] = {
            "value": value,
            "threshold": threshold,
            "status": "healthy" if value >= threshold else "concerning",
        }
    return trends

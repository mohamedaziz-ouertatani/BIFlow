"""Metric-level display facts shared by the Python agents."""

# KPIs whose computed value is a 0-1 fraction that people expect to read as a percentage.
PERCENT_METRICS = frozenset({"on_time_delivery_rate", "loan_good_standing_rate", "churn_rate"})


# Formats a 0-1 fraction as a percentage with at most one decimal (0.9385 -> "93.9%", 0.9 -> "90%").
def format_percent(fraction: float) -> str:
    """Formats a 0-1 fraction as a percentage with at most one decimal place."""
    # Format with one decimal, then strip trailing zeros and a dangling dot:
    # '93.9' stays, '90.0' -> '90.', '90.' -> '90'.
    return f"{fraction * 100:.1f}".rstrip("0").rstrip(".") + "%"

// Maps monetary KPI/metric names to the currency of the dataset they're computed from
// (Olist e-commerce data is in Brazilian Real; the Berka banking data is in Czech Koruna;
// the IBM Telco Customer Churn data is in US Dollars).
const METRIC_CURRENCY: Record<string, string> = {
  total_revenue: "BRL",
  average_order_value: "BRL",
  total_transaction_volume: "CZK",
  average_transaction_value: "CZK",
  average_account_balance: "CZK",
  average_monthly_charges: "USD",
};

// KPIs whose value is a 0-1 fraction that reads better as a percentage (mirrors shared/metrics.py).
const PERCENT_METRICS = new Set(["on_time_delivery_rate", "loan_good_standing_rate", "churn_rate"]);

// Shows a 0-1 fraction as a percentage with at most one decimal (0.2654 -> "26.5%", 0.9 -> "90%").
function formatPercent(fraction: number): string {
  return new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 1 }).format(fraction);
}

// Formats a numeric metric value: rates become percentages, monetary metrics get their
// dataset's currency symbol, everything else falls back to plain locale formatting.
export function formatMetricValue(metricName: string, value: number): string {
  if (PERCENT_METRICS.has(metricName)) {
    return formatPercent(value);
  }
  const currency = METRIC_CURRENCY[metricName];
  if (!currency) {
    return Number.isInteger(value) ? value.toString() : value.toFixed(2);
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(value);
}

// Compact form for space-constrained contexts like chart axis ticks (e.g. "R$4k" instead of "R$4,000.00").
export function formatMetricValueCompact(metricName: string, value: number): string {
  if (PERCENT_METRICS.has(metricName)) {
    return formatPercent(value);
  }
  const currency = METRIC_CURRENCY[metricName];
  if (!currency) {
    return new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 }).format(
      value,
    );
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value);
}

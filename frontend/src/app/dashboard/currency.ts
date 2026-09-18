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

// Formats a numeric metric value: monetary metrics get their dataset's currency symbol,
// everything else falls back to plain locale formatting.
export function formatMetricValue(metricName: string, value: number): string {
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

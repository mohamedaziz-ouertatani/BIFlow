// Maps monetary KPI/metric names to the currency of the dataset they're computed from
// (Olist e-commerce data is in Brazilian Real; the Berka banking data is in Czech Koruna).
const METRIC_CURRENCY: Record<string, string> = {
  total_revenue: "BRL",
  average_order_value: "BRL",
  total_transaction_volume: "CZK",
  average_transaction_value: "CZK",
  average_account_balance: "CZK",
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

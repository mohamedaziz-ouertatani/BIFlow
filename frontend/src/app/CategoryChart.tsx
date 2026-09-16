"use client";

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import styles from "./page.module.css";
import type { CategoryBreakdownPoint } from "./types";

const METRIC_LABELS: Record<string, string> = {
  // e-commerce
  total_revenue: "Revenue",
  average_order_value: "Average order value",
  order_count: "Order volume",
  average_review_score: "Review score",
  on_time_delivery_rate: "On-time delivery rate",
  // banking
  total_transaction_volume: "Transaction volume",
  average_transaction_value: "Average transaction value",
  transaction_count: "Transaction count",
  average_account_balance: "Average account balance",
  loan_good_standing_rate: "Loan good standing rate",
};

// Splits a "{kpi_name}_by_{dimension}" breakdown key into its two parts.
function parseBreakdownKey(key: string): { metric: string; dimension: string } {
  const separatorIndex = key.lastIndexOf("_by_");
  if (separatorIndex === -1) {
    return { metric: key, dimension: "" };
  }
  return {
    metric: key.slice(0, separatorIndex),
    dimension: key.slice(separatorIndex + 4),
  };
}

// Renders a KPI's breakdown by a categorical dimension (e.g. revenue by category) as a horizontal bar chart.
export default function CategoryChart({
  breakdownKey,
  points,
}: {
  breakdownKey: string;
  points: CategoryBreakdownPoint[];
}) {
  const { metric, dimension } = parseBreakdownKey(breakdownKey);
  const metricLabel = METRIC_LABELS[metric] ?? metric;
  const label = dimension ? `${metricLabel} by ${dimension}` : metricLabel;
  const chartHeight = Math.max(120, points.length * 32);

  return (
    <div className={styles.chartCard}>
      <div className={styles.chartLabel}>{label}</div>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={points}
          layout="vertical"
          margin={{ top: 8, right: 24, bottom: 0, left: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 11 }} />
          <YAxis
            type="category"
            dataKey="label"
            tick={{ fontSize: 11 }}
            width={110}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface-raised)",
              border: "1px solid var(--border-strong)",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Bar dataKey="value" fill="var(--accent)" radius={[0, 4, 4, 0]} barSize={20} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

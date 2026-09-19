"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { metricAxisDomain } from "./axes";
import { formatMetricValue, formatMetricValueCompact } from "./currency";
import styles from "./page.module.css";
import type { MonthlyTrendPoint } from "./types";

const METRIC_LABELS: Record<string, string> = {
  // e-commerce
  total_revenue: "Revenue",
  order_count: "Order volume",
  average_review_score: "Review score",
  // banking
  total_transaction_volume: "Transaction volume",
  average_transaction_value: "Average transaction value",
  transaction_count: "Transaction count",
  average_account_balance: "Average account balance",
  loan_good_standing_rate: "Loan good standing rate",
};

// Renders a single metric's month-over-month values as a line chart.
export default function TrendChart({
  metric,
  series,
}: {
  metric: string;
  series: MonthlyTrendPoint[];
}) {
  const label = METRIC_LABELS[metric] ?? metric;

  // ResponsiveContainer stretches the chart to its parent's width (the height is fixed). Axis ticks
  // use the compact format (R$4k) to save space; the tooltip shows the exact formatted value.
  return (
    <div className={styles.chartCard}>
      <div className={styles.chartLabel}>{label}</div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)" }}
            minTickGap={20}
          />
          <YAxis
            domain={metricAxisDomain(metric, "line")}
            tick={{ fontSize: 11, fontFamily: "var(--font-plex-mono)" }}
            width={64}
            tickFormatter={(value: number) => formatMetricValueCompact(metric, value)}
          />
          <Tooltip
            contentStyle={{
              background: "var(--surface-raised)",
              border: "1px solid var(--border-strong)",
              borderRadius: 5,
              fontSize: 12,
              fontFamily: "var(--font-plex-mono)",
            }}
            formatter={(value) => formatMetricValue(metric, Number(value))}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--accent)"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

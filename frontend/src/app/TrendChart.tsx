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
import styles from "./page.module.css";
import type { MonthlyTrendPoint } from "./types";

const METRIC_LABELS: Record<string, string> = {
  total_revenue: "Revenue",
  order_count: "Order volume",
  average_review_score: "Review score",
};

export default function TrendChart({
  metric,
  series,
}: {
  metric: string;
  series: MonthlyTrendPoint[];
}) {
  const label = METRIC_LABELS[metric] ?? metric;

  return (
    <div className={styles.chartCard}>
      <div className={styles.chartLabel}>{label}</div>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={series} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
          <XAxis dataKey="month" tick={{ fontSize: 11 }} minTickGap={20} />
          <YAxis tick={{ fontSize: 11 }} width={48} />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#2f80ed"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export interface MonthlyComparison {
  previous_month: string;
  latest_month: string;
  previous_value: number;
  latest_value: number;
  pct_change: number;
  direction: "increasing" | "decreasing" | "flat" | string;
}

export interface KpiCard {
  name: string;
  label: string;
  value: number | string | null;
  explanation?: string | null;
  comparison?: MonthlyComparison | null;
}

export interface Insight {
  title: string;
  description: string;
  related_kpi: string;
  severity: "info" | "warning" | "critical" | string;
}

export interface MonthlyTrendPoint {
  month: string;
  value: number;
}

export interface DashboardLayout {
  kpi_cards: KpiCard[];
  insights: Insight[];
  monthly_trends: Record<string, MonthlyTrendPoint[]>;
}

export interface KpiCard {
  name: string;
  label: string;
  value: number | string | null;
}

export interface Insight {
  title: string;
  description: string;
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

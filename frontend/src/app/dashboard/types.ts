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
  month?: string | null;
}

export interface MonthlyTrendPoint {
  month: string;
  value: number;
}

export interface CategoryBreakdownPoint {
  label: string;
  value: number;
}

export interface DashboardLayout {
  kpi_cards: KpiCard[];
  insights: Insight[];
  monthly_trends: Record<string, MonthlyTrendPoint[]>;
  category_breakdowns?: Record<string, CategoryBreakdownPoint[]>;
  business_domain?: string;
}

export interface DrillDownResponse {
  total_rows: number;
  columns: string[];
  rows: Record<string, unknown>[];
}

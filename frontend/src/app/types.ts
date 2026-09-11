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

export interface DashboardLayout {
  kpi_cards: KpiCard[];
  insights: Insight[];
}

"use client";

import { useEffect, useState } from "react";
import KpiDetail from "./KpiDetail";
import styles from "./page.module.css";
import QueryBox from "./QueryBox";
import Sidebar from "./Sidebar";
import TrendChart from "./TrendChart";
import type { DashboardLayout, MonthlyComparison } from "./types";

const DIRECTION_ARROW: Record<string, string> = {
  increasing: "▲",
  decreasing: "▼",
  flat: "–",
};

// Shows the month-over-month direction arrow and percent change for a KPI.
function ComparisonBadge({ comparison }: { comparison: MonthlyComparison }) {
  const arrow = DIRECTION_ARROW[comparison.direction] ?? "–";
  return (
    <div
      className={`${styles.comparisonBadge} ${
        styles[`comparison-${comparison.direction}`] ?? ""
      }`}
    >
      {arrow} {Math.abs(comparison.pct_change).toFixed(1)}% vs {comparison.previous_month}
    </div>
  );
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const POLL_INTERVAL_MS = 5000;

type FetchState =
  | { status: "loading" }
  | { status: "no-data" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DashboardLayout };

// Fetches the latest dashboard layout from the API, mapping HTTP/network outcomes to FetchState.
async function fetchDashboard(): Promise<FetchState> {
  try {
    const response = await fetch(`${API_URL}/api/dashboard`, { cache: "no-store" });
    if (response.status === 404) {
      return { status: "no-data" };
    }
    if (!response.ok) {
      return { status: "error", message: `API returned ${response.status}` };
    }
    const data = (await response.json()) as DashboardLayout;
    return { status: "ready", data };
  } catch {
    return { status: "error", message: "Could not reach the dashboard API." };
  }
}

// Formats a KPI value for display: integers as-is, floats to 2 decimals, null as an em dash.
function formatValue(value: number | string | null): string {
  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toString() : value.toFixed(2);
  }
  return value === null ? "—" : value;
}

// Top-level dashboard page: polls the API and renders KPI cards, trends, and insights.
export default function DashboardPage() {
  const [state, setState] = useState<FetchState>({ status: "loading" });
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [selectedKpiName, setSelectedKpiName] = useState<string | null>(null);
  const [askOpen, setAskOpen] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      const result = await fetchDashboard();
      if (!cancelled) {
        setState(result);
        if (result.status === "ready") {
          setLastUpdated(new Date());
        }
      }
    };

    poll();
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className={styles.shell}>
      <Sidebar
        domain={state.status === "ready" ? state.data.business_domain : null}
        lastUpdated={lastUpdated}
        reportUrl={state.status === "ready" ? `${API_URL}/api/report.pdf` : null}
        askOpen={askOpen}
        onToggleAsk={() => setAskOpen((open) => !open)}
      />

      <div
        className={`${styles.contentArea} ${
          askOpen && state.status === "ready" ? styles.contentAreaDrawerOpen : ""
        }`}
      >
        <main className={styles.mainContent}>
          {state.status === "loading" && <p>Loading…</p>}
          {state.status === "no-data" && (
            <p>No dashboard data yet — run the pipeline first.</p>
          )}
          {state.status === "error" && <p className={styles.error}>{state.message}</p>}

          {state.status === "ready" && (
            <>
              <section id="overview-section">
                <p className={styles.sectionLabel}>Overview</p>
                <div className={styles.kpiGrid}>
                  {state.data.kpi_cards.map((card) => (
                    <button
                      key={card.name}
                      type="button"
                      className={styles.kpiCard}
                      onClick={() =>
                        setSelectedKpiName((current) =>
                          current === card.name ? null : card.name
                        )
                      }
                    >
                      <div className={styles.kpiLabel}>{card.label}</div>
                      <div className={styles.kpiValue}>{formatValue(card.value)}</div>
                      {card.comparison && <ComparisonBadge comparison={card.comparison} />}
                    </button>
                  ))}
                </div>

                {selectedKpiName &&
                  (() => {
                    const selectedCard = state.data.kpi_cards.find(
                      (c) => c.name === selectedKpiName
                    );
                    if (!selectedCard) return null;
                    return (
                      <KpiDetail
                        card={selectedCard}
                        trendSeries={state.data.monthly_trends[selectedKpiName]}
                        insights={state.data.insights.filter(
                          (insight) => insight.related_kpi === selectedKpiName
                        )}
                        onClose={() => setSelectedKpiName(null)}
                      />
                    );
                  })()}
              </section>

              {Object.keys(state.data.monthly_trends).length > 0 && (
                <section id="trends-section">
                  <h2 className={styles.subheading}>Trends</h2>
                  <div className={styles.chartGrid}>
                    {Object.entries(state.data.monthly_trends).map(([metric, series]) => (
                      <TrendChart key={metric} metric={metric} series={series} />
                    ))}
                  </div>
                </section>
              )}

              {state.data.insights.length > 0 && (
                <section id="insights-section">
                  <h2 className={styles.subheading}>Insights</h2>
                  <ul className={styles.insightList}>
                    {state.data.insights.map((insight, i) => (
                      <li
                        key={i}
                        className={`${styles.insight} ${
                          styles[`severity-${insight.severity}`] ?? ""
                        }`}
                      >
                        <strong>{insight.title}</strong> — {insight.description}
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </>
          )}
        </main>

        {state.status === "ready" && (
          <aside
            className={`${styles.drawer} ${askOpen ? "" : styles.drawerClosed}`}
            aria-hidden={!askOpen}
          >
            <button
              type="button"
              className={styles.closeButton}
              onClick={() => setAskOpen(false)}
              aria-label="Close ask panel"
            >
              ×
            </button>
            <QueryBox />
          </aside>
        )}
      </div>
    </div>
  );
}

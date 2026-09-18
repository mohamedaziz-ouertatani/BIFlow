"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import CategoryChart from "./CategoryChart";
import { formatMetricValue } from "./currency";
import DrillDownPanel from "./DrillDownPanel";
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

type TabId = "overview" | "trends" | "breakdowns" | "insights";

type FetchState =
  | { status: "loading" }
  | { status: "no-data" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DashboardLayout };

// Fetches the latest dashboard layout from the API, mapping HTTP/network outcomes to FetchState.
async function fetchDashboard(domain: string | null): Promise<FetchState> {
  try {
    const url = domain
      ? `${API_URL}/api/dashboard?domain=${encodeURIComponent(domain)}`
      : `${API_URL}/api/dashboard`;
    const response = await fetch(url, { cache: "no-store" });
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

// Formats a KPI value for display: monetary KPIs get their dataset's currency,
// other numbers fall back to plain formatting, and null becomes an em dash.
function formatValue(name: string, value: number | string | null): string {
  if (typeof value === "number") {
    return formatMetricValue(name, value);
  }
  return value === null ? "—" : value;
}

// Top-level dashboard page: polls the API and renders KPIs, trends, breakdowns, and insights as tabs.
function DashboardContent() {
  const searchParams = useSearchParams();
  const domain = searchParams.get("domain");
  const [state, setState] = useState<FetchState>({ status: "loading" });
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [selectedKpiName, setSelectedKpiName] = useState<string | null>(null);
  const [selectedInsightIndex, setSelectedInsightIndex] = useState<number | null>(null);
  const [askOpen, setAskOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<TabId>("overview");

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      const result = await fetchDashboard(domain);
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
  }, [domain]);

  const handleRefresh = () => {
    fetchDashboard(domain).then((result) => {
      setState(result);
      if (result.status === "ready") {
        setLastUpdated(new Date());
      }
    });
  };

  const data = state.status === "ready" ? state.data : null;
  const trendEntries = useMemo(
    () => Object.entries(data?.monthly_trends ?? {}),
    [data]
  );
  const breakdownEntries = useMemo(
    () => Object.entries(data?.category_breakdowns ?? {}),
    [data]
  );
  const insights = data?.insights ?? [];
  const criticalCount = insights.filter((i) => i.severity === "critical").length;
  const warningCount = insights.filter((i) => i.severity === "warning").length;

  const tabs: { id: TabId; label: string; count: number | null }[] = [
    { id: "overview", label: "Overview", count: data ? data.kpi_cards.length : null },
    { id: "trends", label: "Trends", count: trendEntries.length },
    { id: "breakdowns", label: "Breakdowns", count: breakdownEntries.length },
    { id: "insights", label: "Insights", count: insights.length },
  ];

  return (
    <div className={styles.shell}>
      <Sidebar
        domain={data ? data.business_domain : null}
        lastUpdated={lastUpdated}
        reportUrl={
          data
            ? `${API_URL}/api/report.pdf${domain ? `?domain=${encodeURIComponent(domain)}` : ""}`
            : null
        }
        askOpen={askOpen}
        onToggleAsk={() => setAskOpen((open) => !open)}
        onRefresh={handleRefresh}
      />

      <div
        className={`${styles.contentArea} ${
          askOpen && data ? styles.contentAreaDrawerOpen : ""
        }`}
      >
        <main className={styles.mainContent}>
          {state.status === "loading" && <p>Loading…</p>}
          {state.status === "no-data" && (
            <p>No dashboard data yet — run the pipeline first.</p>
          )}
          {state.status === "error" && <p className={styles.error}>{state.message}</p>}

          {data && (
            <>
              <div
                className={styles.tabBar}
                role="tablist"
                aria-label="Dashboard sections"
                onKeyDown={(event) => {
                  const currentIndex = tabs.findIndex((tab) => tab.id === activeTab);
                  let nextIndex: number | null = null;
                  if (event.key === "ArrowRight") {
                    nextIndex = (currentIndex + 1) % tabs.length;
                  } else if (event.key === "ArrowLeft") {
                    nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
                  } else if (event.key === "Home") {
                    nextIndex = 0;
                  } else if (event.key === "End") {
                    nextIndex = tabs.length - 1;
                  }
                  if (nextIndex !== null) {
                    event.preventDefault();
                    const nextTab = tabs[nextIndex];
                    setActiveTab(nextTab.id);
                    document.getElementById(`tab-${nextTab.id}`)?.focus();
                  }
                }}
              >
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    id={`tab-${tab.id}`}
                    type="button"
                    role="tab"
                    aria-selected={activeTab === tab.id}
                    aria-controls={`panel-${tab.id}`}
                    tabIndex={activeTab === tab.id ? 0 : -1}
                    className={`${styles.tab} ${
                      activeTab === tab.id ? styles.tabActive : ""
                    } ${tab.id === "insights" && criticalCount > 0 ? styles.tabAttention : ""}`}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    {tab.label}
                    {tab.count !== null && (
                      <span className={styles.tabCount}>{tab.count}</span>
                    )}
                  </button>
                ))}
              </div>

              {activeTab === "overview" && (
                <section
                  id="panel-overview"
                  role="tabpanel"
                  aria-labelledby="tab-overview"
                  className={styles.tabPanel}
                >
                  <p className={styles.sectionLabel}>KPIs</p>
                  <div className={styles.kpiGrid}>
                    {data.kpi_cards.map((card) => (
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
                        <div className={styles.kpiValue}>{formatValue(card.name, card.value)}</div>
                        {card.comparison && <ComparisonBadge comparison={card.comparison} />}
                      </button>
                    ))}
                    {data.kpi_cards.length === 0 && (
                      <p className={styles.noTrend}>No KPIs computed for this run.</p>
                    )}
                  </div>

                  {selectedKpiName &&
                    (() => {
                      const selectedCard = data.kpi_cards.find(
                        (c) => c.name === selectedKpiName
                      );
                      if (!selectedCard) return null;
                      return (
                        <KpiDetail
                          card={selectedCard}
                          trendSeries={data.monthly_trends[selectedKpiName]}
                          insights={data.insights.filter(
                            (insight) => insight.related_kpi === selectedKpiName
                          )}
                          domain={domain}
                          onClose={() => setSelectedKpiName(null)}
                        />
                      );
                    })()}
                </section>
              )}

              {activeTab === "trends" && (
                <section
                  id="panel-trends"
                  role="tabpanel"
                  aria-labelledby="tab-trends"
                  className={styles.tabPanel}
                >
                  <p className={styles.sectionLabel}>Monthly trends</p>
                  {trendEntries.length > 0 ? (
                    <div className={styles.chartGrid}>
                      {trendEntries.map(([metric, series]) => (
                        <TrendChart key={metric} metric={metric} series={series} />
                      ))}
                    </div>
                  ) : (
                    <p className={styles.noTrend}>No trend data available for this run.</p>
                  )}
                </section>
              )}

              {activeTab === "breakdowns" && (
                <section
                  id="panel-breakdowns"
                  role="tabpanel"
                  aria-labelledby="tab-breakdowns"
                  className={styles.tabPanel}
                >
                  <p className={styles.sectionLabel}>Category breakdowns</p>
                  {breakdownEntries.length > 0 ? (
                    <div className={styles.breakdownsGrid}>
                      {breakdownEntries.map(([breakdownKey, points]) => (
                        <CategoryChart
                          key={breakdownKey}
                          breakdownKey={breakdownKey}
                          points={points}
                        />
                      ))}
                    </div>
                  ) : (
                    <p className={styles.noTrend}>No category breakdowns available for this run.</p>
                  )}
                </section>
              )}

              {activeTab === "insights" && (
                <section
                  id="panel-insights"
                  role="tabpanel"
                  aria-labelledby="tab-insights"
                  className={styles.tabPanel}
                >
                  <p className={styles.sectionLabel}>
                    Insights
                    {(criticalCount > 0 || warningCount > 0) && (
                      <span className={styles.sectionLabelDetail}>
                        {criticalCount > 0 && ` ${criticalCount} critical`}
                        {criticalCount > 0 && warningCount > 0 && ","}
                        {warningCount > 0 && ` ${warningCount} warning`}
                      </span>
                    )}
                  </p>
                  {insights.length > 0 ? (
                    <ul className={styles.insightList}>
                      {insights.map((insight, i) => {
                        const isDrillable = insight.related_kpi !== "";
                        const isSelected = selectedInsightIndex === i;
                        return (
                          <li key={i} className={styles.insightRow}>
                            {isDrillable ? (
                              <button
                                type="button"
                                className={`${styles.insight} ${
                                  styles[`severity-${insight.severity}`] ?? ""
                                }`}
                                aria-expanded={isSelected}
                                onClick={() =>
                                  setSelectedInsightIndex(isSelected ? null : i)
                                }
                              >
                                <span className={styles.insightText}>
                                  <strong>{insight.title}</strong> — {insight.description}
                                </span>
                              </button>
                            ) : (
                              <div
                                className={`${styles.insight} ${
                                  styles[`severity-${insight.severity}`] ?? ""
                                }`}
                              >
                                <span className={styles.insightText}>
                                  <strong>{insight.title}</strong> — {insight.description}
                                </span>
                              </div>
                            )}
                            {isDrillable && isSelected && domain && (
                              <div className={styles.insightDrillDown}>
                                <DrillDownPanel
                                  domain={domain}
                                  kpiName={insight.related_kpi}
                                  month={insight.month}
                                />
                              </div>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  ) : (
                    <p className={styles.noTrend}>No insights generated for this run.</p>
                  )}
                </section>
              )}
            </>
          )}
        </main>

        {data && (
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
            <QueryBox domain={domain} />
          </aside>
        )}
      </div>
    </div>
  );
}

// Wraps DashboardContent in Suspense: required because it reads the domain
// from useSearchParams, which Next.js must be able to bail out of during
// static prerendering.
export default function DashboardPage() {
  return (
    <Suspense fallback={<div className={styles.shell}><p>Loading…</p></div>}>
      <DashboardContent />
    </Suspense>
  );
}

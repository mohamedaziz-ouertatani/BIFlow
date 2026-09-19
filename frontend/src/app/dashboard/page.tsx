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
import type { DashboardLayout, Insight, KpiCard, MonthlyComparison } from "./types";

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

type Attention = "critical" | "warning" | "info" | "none";

const ATTENTION_RANK: Record<Attention, number> = { critical: 3, warning: 2, info: 1, none: 0 };

// A KPI's attention level is the highest severity among the insights that reference it.
function attentionFor(kpiName: string, insights: Insight[]): { level: Attention; count: number } {
  let level: Attention = "none";
  let count = 0;
  for (const insight of insights) {
    if (insight.related_kpi !== kpiName) continue;
    count += 1;
    const severity: Attention =
      insight.severity === "critical" || insight.severity === "warning" ? insight.severity : "info";
    if (ATTENTION_RANK[severity] > ATTENTION_RANK[level]) level = severity;
  }
  return { level, count };
}

function severityOf(insight: Insight): Attention {
  return insight.severity === "critical" || insight.severity === "warning" ? insight.severity : "info";
}

function findingsText(level: Attention, count: number): string {
  if (count === 0) return "No findings";
  return `${count} ${level === "none" ? "info" : level}`;
}

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
    // no-store: never serve a cached copy, the dashboard must show the latest pipeline run.
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

// Top-level dashboard page: polls the API and renders findings, the KPI wall, trends and breakdowns.
function DashboardContent() {
  const searchParams = useSearchParams();
  const domain = searchParams.get("domain");
  const [state, setState] = useState<FetchState>({ status: "loading" });
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [selectedKpiName, setSelectedKpiName] = useState<string | null>(null);
  const [selectedInsightIndex, setSelectedInsightIndex] = useState<number | null>(null);
  const [askOpen, setAskOpen] = useState(true);

  useEffect(() => {
    // `cancelled` guards against a slow response arriving after the domain changed or the page
    // unmounted, which would overwrite newer state with stale data.
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

  const wall = useMemo(() => {
    const cards = data?.kpi_cards ?? [];
    return cards
      // `index` is the card's original position, so its KPI·NN code stays fixed after re-sorting.
      .map((card, index) => ({ card, index, ...attentionFor(card.name, insights) }))
      // Highest attention first; `||` falls through to the original index when the levels tie,
      // so equal tiles keep a stable order.
      .sort((a, b) => ATTENTION_RANK[b.level] - ATTENTION_RANK[a.level] || a.index - b.index);
  }, [data, insights]);

  const rankedInsights = insights
    .map((insight, index) => ({ insight, index }))
    .sort(
      (a, b) =>
        ATTENTION_RANK[severityOf(b.insight)] - ATTENTION_RANK[severityOf(a.insight)] ||
        a.index - b.index
    );

  const selectedCard = data?.kpi_cards.find((c) => c.name === selectedKpiName) ?? null;

  const openKpi = (name: string) => {
    setSelectedKpiName(name);
    // Wait one frame so the detail panel exists in the DOM before scrolling to it. `?.scrollIntoView?.`
    // because jsdom (the Jest test DOM) doesn't implement scrollIntoView.
    requestAnimationFrame(() =>
      document.getElementById("audit-bay")?.scrollIntoView?.({ block: "nearest", behavior: "smooth" })
    );
  };

  return (
    <div className={styles.shell}>
      <div className={styles.scanlines} aria-hidden="true" />
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
          {state.status === "loading" && <p className={styles.statusLine}>Loading…</p>}
          {state.status === "no-data" && (
            <p className={styles.statusLine}>No dashboard data yet — run the pipeline first.</p>
          )}
          {state.status === "error" && (
            <p className={`${styles.statusLine} ${styles.error}`}>{state.message}</p>
          )}

          {data && (
            <>
              <section className={styles.block} aria-labelledby="findings-heading">
                <div className={styles.blockHead}>
                  <h2 id="findings-heading" className={styles.blockTitle}>
                    Findings
                  </h2>
                  <span className={styles.blockMeta}>
                    {criticalCount === 0 && warningCount === 0
                      ? `${insights.length} logged`
                      : [
                          criticalCount > 0 ? `${criticalCount} critical` : null,
                          warningCount > 0 ? `${warningCount} warning` : null,
                        ]
                          .filter(Boolean)
                          .join(" · ")}
                  </span>
                </div>
                {insights.length > 0 ? (
                  <ul className={styles.insightList}>
                    {rankedInsights.map(({ insight, index: i }) => {
                      const isDrillable = insight.related_kpi !== "";
                      const isSelected = selectedInsightIndex === i;
                      return (
                        <li key={i} className={styles.insightRow}>
                          {isDrillable ? (
                            <div className={styles.insightLine}>
                              <button
                                type="button"
                                className={`${styles.insight} ${
                                  styles[`severity-${insight.severity}`] ?? ""
                                }`}
                                aria-expanded={isSelected}
                                onClick={() => setSelectedInsightIndex(isSelected ? null : i)}
                              >
                                <span className={styles.insightText}>
                                  <strong>{insight.title}</strong> — {insight.description}
                                </span>
                              </button>
                              <button
                                type="button"
                                className={styles.locateButton}
                                aria-label={`Open ${insight.related_kpi} tile`}
                                onClick={() => openKpi(insight.related_kpi)}
                              >
                                Open KPI
                              </button>
                            </div>
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

              <section className={styles.block} aria-labelledby="wall-heading">
                <div className={styles.blockHead}>
                  <h2 id="wall-heading" className={styles.blockTitle}>
                    KPI telemetry
                  </h2>
                  <span className={styles.blockMeta}>sorted by attention</span>
                </div>
                <div className={styles.wall}>
                  {wall.map(({ card, index, level, count }) => (
                    <KpiTile
                      key={card.name}
                      card={card}
                      code={`KPI·${String(index + 1).padStart(2, "0")}`}
                      level={level}
                      count={count}
                      selected={selectedKpiName === card.name}
                      onSelect={() =>
                        setSelectedKpiName((current) => (current === card.name ? null : card.name))
                      }
                    />
                  ))}
                  {wall.length === 0 && (
                    <p className={styles.noTrend}>No KPIs computed for this run.</p>
                  )}
                </div>

                {selectedCard && (
                  <div id="audit-bay">
                    <KpiDetail
                      card={selectedCard}
                      trendSeries={data.monthly_trends[selectedCard.name]}
                      insights={data.insights.filter(
                        (insight) => insight.related_kpi === selectedCard.name
                      )}
                      domain={domain}
                      onClose={() => setSelectedKpiName(null)}
                    />
                  </div>
                )}
              </section>

              <section className={styles.block} aria-labelledby="trends-heading">
                <div className={styles.blockHead}>
                  <h2 id="trends-heading" className={styles.blockTitle}>
                    Monthly trends
                  </h2>
                  <span className={styles.blockMeta}>{trendEntries.length}</span>
                </div>
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

              <section className={styles.block} aria-labelledby="breakdowns-heading">
                <div className={styles.blockHead}>
                  <h2 id="breakdowns-heading" className={styles.blockTitle}>
                    Category breakdowns
                  </h2>
                  <span className={styles.blockMeta}>{breakdownEntries.length}</span>
                </div>
                {breakdownEntries.length > 0 ? (
                  <div className={styles.breakdownsGrid}>
                    {breakdownEntries.map(([breakdownKey, points]) => (
                      <CategoryChart key={breakdownKey} breakdownKey={breakdownKey} points={points} />
                    ))}
                  </div>
                ) : (
                  <p className={styles.noTrend}>No category breakdowns available for this run.</p>
                )}
              </section>
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

// One KPI as a status-lit tile: value, delta, one-line formula, and its finding count.
function KpiTile({
  card,
  code,
  level,
  count,
  selected,
  onSelect,
}: {
  card: KpiCard;
  code: string;
  level: Attention;
  count: number;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      className={`${styles.tile} ${styles[`tile-${level}`]} ${selected ? styles.tileSelected : ""}`}
      aria-pressed={selected}
      onClick={onSelect}
    >
      <span className={styles.tileHead}>
        <span className={styles.tileLight} aria-hidden="true" />
        <span className={styles.tileCode}>{code}</span>
        <span className={styles.tileFindings}>{findingsText(level, count)}</span>
      </span>
      <span className={styles.kpiLabel}>{card.label}</span>
      <span className={styles.kpiValue}>{formatValue(card.name, card.value)}</span>
      {card.comparison && <ComparisonBadge comparison={card.comparison} />}
      {card.explanation && (
        <span className={styles.tileFormula} title={card.explanation}>
          {card.explanation}
        </span>
      )}
    </button>
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

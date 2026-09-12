"use client";

import { useEffect, useState } from "react";
import styles from "./page.module.css";
import TrendChart from "./TrendChart";
import type { DashboardLayout } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const POLL_INTERVAL_MS = 5000;

type FetchState =
  | { status: "loading" }
  | { status: "no-data" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DashboardLayout };

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

function formatValue(value: number | string | null): string {
  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toString() : value.toFixed(2);
  }
  return value === null ? "—" : value;
}

export default function DashboardPage() {
  const [state, setState] = useState<FetchState>({ status: "loading" });
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

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
    <main className={styles.main}>
      <h1 className={styles.title}>BIFlow Dashboard</h1>

      {state.status === "loading" && <p>Loading…</p>}
      {state.status === "no-data" && (
        <p>No dashboard data yet — run the pipeline first.</p>
      )}
      {state.status === "error" && <p className={styles.error}>{state.message}</p>}

      {state.status === "ready" && (
        <>
          <div className={styles.kpiGrid}>
            {state.data.kpi_cards.map((card) => (
              <div key={card.name} className={styles.kpiCard}>
                <div className={styles.kpiLabel}>{card.label}</div>
                <div className={styles.kpiValue}>{formatValue(card.value)}</div>
              </div>
            ))}
          </div>

          {Object.keys(state.data.monthly_trends).length > 0 && (
            <section>
              <h2 className={styles.subheading}>Trends</h2>
              <div className={styles.chartGrid}>
                {Object.entries(state.data.monthly_trends).map(([metric, series]) => (
                  <TrendChart key={metric} metric={metric} series={series} />
                ))}
              </div>
            </section>
          )}

          {state.data.insights.length > 0 && (
            <section>
              <h2 className={styles.subheading}>Insights</h2>
              <ul className={styles.insightList}>
                {state.data.insights.map((insight, i) => (
                  <li
                    key={i}
                    className={`${styles.insight} ${styles[`severity-${insight.severity}`] ?? ""}`}
                  >
                    <strong>{insight.title}</strong> — {insight.description}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {lastUpdated && (
            <p className={styles.lastUpdated}>
              Last updated {lastUpdated.toLocaleTimeString()} (polling every{" "}
              {POLL_INTERVAL_MS / 1000}s)
            </p>
          )}
        </>
      )}
    </main>
  );
}

"use client";

import { useState } from "react";
import styles from "./page.module.css";
import type { DrillDownResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type DrillDownState =
  | { status: "collapsed" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: DrillDownResponse };

// Fetches the rows behind a KPI (optionally scoped to one month) from /api/drilldown.
async function fetchDrillDown(
  domain: string,
  kpiName: string,
  month?: string | null
): Promise<DrillDownState> {
  try {
    const params = new URLSearchParams({ domain, kpi: kpiName });
    if (month) params.set("month", month);
    const response = await fetch(`${API_URL}/api/drilldown?${params}`, { cache: "no-store" });
    if (!response.ok) {
      const body = (await response.json().catch(() => null)) as { detail?: string } | null;
      return { status: "error", message: body?.detail ?? `API returned ${response.status}` };
    }
    const data = (await response.json()) as DrillDownResponse;
    return { status: "ready", data };
  } catch {
    return { status: "error", message: "Could not reach the dashboard API." };
  }
}

// Collapsed-by-default panel: on expand, fetches and shows the raw rows behind a KPI's value.
export default function DrillDownPanel({
  domain,
  kpiName,
  month,
  formula,
}: {
  domain: string;
  kpiName: string;
  month?: string | null;
  formula?: string | null;
}) {
  const [state, setState] = useState<DrillDownState>({ status: "collapsed" });

  const handleToggle = () => {
    if (state.status === "collapsed") {
      setState({ status: "loading" });
      fetchDrillDown(domain, kpiName, month).then(setState);
    } else {
      setState({ status: "collapsed" });
    }
  };

  return (
    <div className={styles.drillDown}>
      <button type="button" className={styles.drillToggle} onClick={handleToggle}>
        {state.status === "collapsed" ? "View underlying rows ▸" : "Hide underlying rows ▾"}
      </button>

      {state.status === "loading" && <p className={styles.noTrend}>Loading…</p>}
      {state.status === "error" && <p className={styles.error}>{state.message}</p>}

      {state.status === "ready" && (
        <div className={styles.drillPanel}>
          <p className={styles.drillSummary}>
            {formula && <span>{formula}</span>}
            {month && <span> · {month}</span>}
            {(formula || month) && " · "}
            {state.data.total_rows} row{state.data.total_rows === 1 ? "" : "s"} matched
            {state.data.total_rows > state.data.rows.length &&
              ` (showing first ${state.data.rows.length})`}
          </p>
          {state.data.rows.length > 0 ? (
            <div className={styles.drillTableWrap}>
              <table className={styles.drillTable}>
                <thead>
                  <tr>
                    {state.data.columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {state.data.rows.map((row, i) => (
                    <tr key={i}>
                      {state.data.columns.map((col) => (
                        <td key={col}>{String(row[col] ?? "")}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className={styles.noTrend}>No rows matched.</p>
          )}
        </div>
      )}
    </div>
  );
}

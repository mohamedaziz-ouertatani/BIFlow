"use client";

import styles from "./page.module.css";
import TrendChart from "./TrendChart";
import type { Insight, KpiCard, MonthlyTrendPoint } from "./types";

// Expanded panel for a selected KPI: shows its explanation, trend chart, and related insights.
export default function KpiDetail({
  card,
  trendSeries,
  insights,
  onClose,
}: {
  card: KpiCard;
  trendSeries: MonthlyTrendPoint[] | undefined;
  insights: Insight[];
  onClose: () => void;
}) {
  return (
    <section className={styles.detailPanel} data-testid="kpi-detail">
      <div className={styles.detailHeader}>
        <h2 className={styles.subheading}>{card.label}</h2>
        <button
          type="button"
          className={styles.closeButton}
          onClick={onClose}
          aria-label="Close KPI details"
        >
          ×
        </button>
      </div>

      {card.explanation && <p className={styles.explanation}>{card.explanation}</p>}

      {trendSeries ? (
        <TrendChart metric={card.name} series={trendSeries} />
      ) : (
        <p className={styles.noTrend}>No trend data available for this KPI.</p>
      )}

      {insights.length > 0 && (
        <ul className={styles.insightList}>
          {insights.map((insight, i) => (
            <li
              key={i}
              className={`${styles.insight} ${styles[`severity-${insight.severity}`] ?? ""}`}
            >
              <strong>{insight.title}</strong> — {insight.description}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

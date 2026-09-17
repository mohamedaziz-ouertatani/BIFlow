"use client";

import styles from "./page.module.css";

// Left sidebar: brand/domain identity plus quick actions (refresh, PDF export, ask toggle).
export default function Sidebar({
  domain,
  lastUpdated,
  reportUrl,
  askOpen,
  onToggleAsk,
  onRefresh,
}: {
  domain?: string | null;
  lastUpdated: Date | null;
  reportUrl: string | null;
  askOpen: boolean;
  onToggleAsk: () => void;
  onRefresh: () => void;
}) {
  return (
    <aside className={styles.sidebar} aria-label="Dashboard navigation">
      <div className={styles.sidebarBrand}>
        BIFlow
        {domain && <span className={styles.domainBadge}>{domain}</span>}
      </div>

      <div className={styles.sidebarActions}>
        <button type="button" className={styles.sidebarNavLink} onClick={onRefresh}>
          Refresh now
        </button>
        <button
          type="button"
          className={styles.sidebarNavLink}
          onClick={onToggleAsk}
          aria-pressed={askOpen}
        >
          {askOpen ? "Hide ask panel" : "Ask the dashboard"}
        </button>
        {reportUrl && (
          <a className={styles.reportLink} href={reportUrl} download="biflow_report.pdf">
            Download PDF report
          </a>
        )}
        {lastUpdated && (
          <p className={styles.sidebarUpdated}>Updated {lastUpdated.toLocaleTimeString()}</p>
        )}
      </div>
    </aside>
  );
}

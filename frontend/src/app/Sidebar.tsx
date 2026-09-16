"use client";

import { useEffect, useState } from "react";
import styles from "./page.module.css";

const NAV_SECTIONS = [
  { id: "overview-section", label: "Overview" },
  { id: "trends-section", label: "Trends" },
  { id: "breakdowns-section", label: "Breakdowns" },
  { id: "insights-section", label: "Insights" },
];

// Left sidebar: brand/domain, scroll-spy section nav, and quick actions (PDF export, ask toggle).
export default function Sidebar({
  domain,
  lastUpdated,
  reportUrl,
  askOpen,
  onToggleAsk,
}: {
  domain?: string | null;
  lastUpdated: Date | null;
  reportUrl: string | null;
  askOpen: boolean;
  onToggleAsk: () => void;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);

  // Tracks which section is currently in view so its nav link can be highlighted.
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;

    const elements = NAV_SECTIONS.map((section) => document.getElementById(section.id)).filter(
      (el): el is HTMLElement => el !== null
    );
    if (elements.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const mostVisible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (mostVisible) {
          setActiveId(mostVisible.target.id);
        }
      },
      { rootMargin: "-15% 0px -70% 0px", threshold: [0, 0.25, 0.5, 1] }
    );

    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <aside className={styles.sidebar} aria-label="Dashboard navigation">
      <div className={styles.sidebarBrand}>
        BIFlow
        {domain && <span className={styles.domainBadge}>{domain}</span>}
      </div>

      <nav className={styles.sidebarNav} aria-label="Dashboard sections">
        {NAV_SECTIONS.map((section) => (
          <button
            key={section.id}
            type="button"
            className={`${styles.sidebarNavLink} ${
              activeId === section.id ? styles.sidebarNavLinkActive : ""
            }`}
            onClick={() => scrollToSection(section.id)}
          >
            {section.label}
          </button>
        ))}
      </nav>

      <div className={styles.sidebarActions}>
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

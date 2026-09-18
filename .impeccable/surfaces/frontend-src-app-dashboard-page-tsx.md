---
version: 1
slug: "frontend-src-app-dashboard-page-tsx"
primary_target: "frontend/src/app/dashboard/page.tsx"
related_targets: ["frontend/src/app/dashboard/page.module.css"]
---

# Dashboard — surface brief

Scope: `frontend/src/app/dashboard/page.tsx` (route `/dashboard`), styled by `page.module.css` with the components in that folder. Mode: Operate (dashboard; the visitor reads business state and audits numbers).

Audience/job: an academic evaluator (one sitting) plus analysts exploring. Task: see what needs attention, understand any number's formula, drill to the rows behind it, ask free-text questions. Content is real: `/api/dashboard` KPI cards (value, MoM comparison, explanation/formula), insights (severity, related_kpi, month), monthly trends, category breakdowns, `/api/drilldown` rows, `/api/query` Q&A, PDF report. No invented data. Priorities confirmed by user: insights/anomalies first-class, explainability at a glance, fast first-time comprehension.

Constraints: preserve polling (5s), domain param, refresh, PDF link, drill-down (KPI + insight), Ask panel with hide toggle, no-data/error states, keyboard access, print behaviour. The world is settled by the user: extend the landing's Mission Control world to the dashboard (this supersedes the Audit Console section of DESIGN.md for this route).

Structure (roll, seed key a5876806, lead index 4): Telemetry Wall. No tabs. Findings log on top, KPI wall of status-lit tiles sorted by attention, in-place audit bay for the selected KPI, trends and breakdowns below, Ask docked as a command line at the bottom.

## Direction contract

THESIS: The dashboard is a telemetry wall where attention is the sort order: every KPI is a status-lit subsystem tile that carries its own formula, and findings read as a live log above it, so "what needs eyes and why" is answered before anything is clicked. Refuses the tab-per-section report layout and the equal-weight card grid.

OWN-WORLD: The landing's instrument-black ground (`#05070a`, panels `#0b0f14`/`#121820`, hairline bezels, scanline texture at rest) with one rule for color: amber = needs attention (warning), red = critical, green/red deltas for month-over-month direction, phosphor white-cyan is the data ink (chart lines, bars, selection) and never a status. Geist Sans for labels and copy; IBM Plex Mono tabular for values, formulas, codes, timestamps, log lines. Panels are recessed bezels with inset hairlines, radius 4px, no soft shadows.

STORY: The viewer arrives and reads the findings log (n critical, n warning) and sees the wall already sorted so the worst tile is top-left with a red light. Each tile shows value, delta and its formula in one line, so numbers are traceable without opening anything. Opening a tile lifts an audit bay with trend, formula, related findings and the rows behind the number. The command line at the bottom answers questions about the same data.

FIRST VIEWPORT: Slim top bar (callsign, domain badge, refresh, ask toggle, PDF, updated clock). Below it the Findings log (max about 5 rows visible, severity-sorted, critical first), then the KPI wall as a 4-column grid of tiles (2 on tablet, 1 on phone), worst first. Ask command line docked to the viewport bottom edge. Primary action is opening a tile or finding; there is no hero.

FORM: Telemetry Wall, dealt as THE ROLL (index 4 of my ranked list; seed key a5876806), chosen by the user. Honest risk: status-lit tiles imply per-KPI health; status is derived only from insight severity, and KPIs with no findings read as "No findings", never as "healthy".

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

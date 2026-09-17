---
name: BIFlow Dashboard
description: An instrument-panel audit console for a multi-agent BI pipeline where every number traces to a formula.
colors:
  lab-paper: "#eef0ee"
  ink: "#10141a"
  ink-muted: "#5c6470"
  panel: "#fbfbfa"
  panel-raised: "#ffffff"
  hairline: "rgba(16, 20, 26, 0.13)"
  hairline-strong: "rgba(16, 20, 26, 0.24)"
  signal-cyan: "#0891a8"
  signal-cyan-strong: "#066579"
  signal-cyan-soft: "rgba(8, 145, 168, 0.12)"
  status-success: "#1a7a4c"
  status-warning: "#a3690a"
  status-danger: "#c23a3a"
typography:
  headline:
    fontFamily: "Geist Sans, -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Geist Sans, -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 600
  body:
    fontFamily: "Geist Sans, -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 400
  label:
    fontFamily: "IBM Plex Mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "0.72rem"
    fontWeight: 500
    letterSpacing: "0.08em"
  numeral:
    fontFamily: "IBM Plex Mono, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "1.7rem"
    fontWeight: 600
    fontFeature: "tabular-nums"
rounded:
  sm: "5px"
  md: "8px"
  lg: "10px"
spacing:
  xs: "0.35rem"
  sm: "0.6rem"
  md: "1rem"
  lg: "1.75rem"
  xl: "2.5rem"
components:
  button-primary:
    backgroundColor: "{colors.signal-cyan}"
    textColor: "{colors.panel}"
    rounded: "{rounded.sm}"
    padding: "0.65rem 1.2rem"
  button-primary-hover:
    backgroundColor: "{colors.signal-cyan-strong}"
    textColor: "{colors.panel}"
    rounded: "{rounded.sm}"
    padding: "0.65rem 1.2rem"
  button-ghost:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: "0.5rem 0.85rem"
  nav-link:
    backgroundColor: "transparent"
    textColor: "{colors.ink-muted}"
    typography: "{typography.body}"
    rounded: "{rounded.sm}"
    padding: "0.5rem 0.6rem"
  nav-link-active:
    backgroundColor: "transparent"
    textColor: "{colors.signal-cyan}"
    padding: "0.5rem 0.6rem"
  kpi-card:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    padding: "1.15rem 1.25rem"
---

# Design System: BIFlow Dashboard

## Overview

**Creative North Star: "The Audit Console"**

BIFlow's product truth is that every KPI is a formula, run by an auditable agent, not a black box — so the dashboard is built as an instrument panel / lab-ledger, not a generic SaaS card grid. Surfaces are flat lab-paper (light) or dark-instrument black (dark, via `prefers-color-scheme`), separated by hairline rules rather than floating shadows, with one committed signal-cyan accent reserved strictly for "this is live." The confirmed anti-reference is the prior dashboard generation (adaptive theme, soft nav highlight, stat-tile cards with individual shadows) — that shell is explicitly not the target; this system replaces its soft highlight sidebar with a schematic connector line, and its floating cards with a shared-hairline grid.

The signature move is the type split: every numeral — KPI values, chart axis ticks and tooltips, timestamps — is set in IBM Plex Mono with tabular numerals, while every label, heading, and sentence of prose runs in Geist Sans. This isn't decorative; it makes "this number was computed, not guessed" legible at a glance, which is the whole pitch of a multi-agent pipeline that traces numbers back to formulas.

Density is close but not cramped: a fixed 280px sidebar and fixed 400px query drawer bracket a fluid, capped-width reading column, so the KPI grid, trend/breakdown charts, and insight ledger all read as instrument readouts rather than dashboard widgets.

**2026-09-17 — information architecture revision.** The colors, typography, and component tokens below are unchanged. What changed is how the reading column is organized: the dashboard moved from one continuous vertical scroll (with a sidebar scroll-spy nav highlighting the section in view) to a four-tab ARIA tabs widget (Overview/Trends/Breakdowns/Insights) at the top of the main column. The sidebar's schematic connector nav — described below as a signature component — was retired as part of this change, since there is no longer a single scrolling page for it to track; see **Layout** and **Components → Tab Bar** for the current structure. This is a structural change, not a new visual world.

**Key Characteristics:**
- Flat lab-paper/instrument-black surfaces, hairline-separated, not shadow-separated
- One signal-cyan accent, reserved for "live" state only
- Numerals in IBM Plex Mono (tabular), everything else in Geist Sans
- Tightened radii (5/8/10px) read as instrument-panel, not bubbly SaaS
- Insight severity and KPI formulas are typographic ledger marks, not colored side-tabs
- Content is organized as four ARIA tabs (Overview/Trends/Breakdowns/Insights), not a single scrolling page

## Colors

Two neutrals (lab-paper light / instrument-black dark) carry nearly the whole surface; color is spent almost entirely on one accent and three status hues that are deliberately kept apart from it.

### Primary
- **Signal Cyan** (`#0891a8` light / `#22d3ee` dark): the single accent. Used only for "live/active" signal — the active tab's underline, count badge, and focus rings; focus rings on inputs; the domain badge outline; chart line/bar fill; and the "Formula" label on the KPI explanation block. Never doubles as a status color.

### Neutral
- **Lab Paper** (`#eef0ee` background light / `#08090b` dark): the page background.
- **Ink** (`#10141a` foreground light / `#e7ebee` dark): primary text.
- **Ink Muted** (`#5c6470` light / `#838c99` dark): secondary text — labels, timestamps, section labels, chart ticks.
- **Panel** (`#fbfbfa` light / `#0e1114` dark): default card/sidebar/drawer surface.
- **Panel Raised** (`#ffffff` light / `#13171b` dark): hover state and the KPI detail flyout, the one surface that gets a shadow.
- **Hairline** (`rgba(16,20,26,0.13)` light / `rgba(231,235,238,0.09)` dark): default borders, the KPI-grid rule lines, and the tab bar's baseline rule.
- **Hairline Strong** (`rgba(16,20,26,0.24)` light / `rgba(231,235,238,0.18)` dark): input borders, dashed ledger rules.

Status colors — **Success** (`#1a7a4c`/`#34d399`), **Warning** (`#a3690a`/`#eab308`), **Danger** (`#c23a3a`/`#f87171`) — mark KPI trend direction and insight severity, and now also the tab bar's "attention" state (the Insights tab's count badge turns danger when at least one insight is `critical`). They are chosen to sit visually apart from signal-cyan on both light and dark palettes on purpose.

### Named Rules
**The One Accent Rule.** Signal-cyan means "live" and nothing else: active tab/nav state, focus, and the formula label. It never represents success, warning, or danger, and status colors never borrow it — so a viewer can always read cyan as "this is the thing currently active," not as a fourth status color.

## Typography

**Body Font:** Geist Sans (with -apple-system, BlinkMacSystemFont, Segoe UI, Arial, sans-serif)
**Label/Mono Font:** IBM Plex Mono (with ui-monospace, SFMono-Regular, Menlo, Consolas, monospace), weights 400/500/600, `font-variant-numeric: tabular-nums`

**Character:** A plain, confident UI sans paired with a monospace ledger face reserved for anything that is a measurement — the pairing itself is the explainability cue.

### Hierarchy
- **Headline** (700, 1.5rem, tight tracking `-0.01em`): the page title ("BIFlow" + domain badge).
- **Title** (600, 1.05rem): section subheadings ("Trends", "Breakdowns", KPI detail panel title).
- **Body** (400–500, 0.85–0.9rem, 600 for tab labels): tab labels, insight text, query answers.
- **Label** (500, 0.68–0.78rem, uppercase, `0.04–0.08em` tracking, mono): section labels ("§ Overview"), the domain badge, the "Formula" label, KPI card labels, tab count badges.
- **Numeral** (600, 1.7–1.85rem, mono, tabular-nums): KPI values; the same tabular treatment (at smaller sizes) drives chart axis ticks, tooltips, comparison-badge percentages, tab count badges, and the "Updated HH:MM:SS" timestamp.

### Named Rules
**The Mono-Numerals Rule.** Anything that is a measured or timestamped value — KPI values, chart ticks/tooltips, percent-change badges, tab counts, "Updated" timestamps — is set in IBM Plex Mono with tabular numerals. Anything that is a label, heading, or sentence is Geist Sans. No component mixes the two within the same text run.

## Layout

Three-column shell: a fixed 280px left sidebar, a fluid main column capped at 880px and centered in the remaining space, and a fixed 400px right drawer ("Ask the dashboard") that slides in via `transform: translateX()`, not an animated margin — margin-right on the content area is set directly (no transition) to avoid layout thrash while the drawer's own transform animates over 0.2s. Below 900px the sidebar collapses to a static horizontal row of brand + action buttons, the drawer becomes a static stacked block instead of an overlay, and main-content padding tightens from `2rem 1.75rem 4rem` to `1.5rem 1.25rem 3rem`.

**Information architecture (revised 2026-09-17).** The main column's content is a `role="tablist"` of four top-level tabs — Overview, Trends, Breakdowns, Insights — rendered above a single `role="tabpanel"` for the active tab, with arrow-key/Home/End roving-tabindex keyboard navigation. Each tab carries a mono, tabular-nums count badge (e.g. "Insights 3"); the Insights tab's badge switches to the danger hue when at least one insight is `critical`, so severity is visible without opening the tab. This replaced the previous single continuous scroll (Overview → Trends → Breakdowns → Insights stacked, with the sidebar driving an IntersectionObserver scroll-spy nav) — the sidebar no longer carries section navigation, only brand identity and action controls (manual "Refresh now", "Ask the dashboard" toggle, PDF export link, last-updated stamp). Insights, previously the last section on a long page, is now reachable in one click as a first-class tab. Because content is tabbed rather than stacked, no single view is an unbounded page anymore: the Breakdowns tab's chart grid caps its own height (`max-height: calc(100vh - 14rem)`) and scrolls internally rather than extending the page, and each category chart's plotted height is capped (`Math.min(320, Math.max(120, points.length * 32))`, wrapped in a `max-height: 320px` body) so a chart can no longer grow tall enough to be sliced across a print/PDF page boundary. A `@media print` block hides the tab bar, sidebar, and drawer, forces the Breakdowns grid to a single scrollable-off column, and adds `break-inside: avoid` to KPI cards, chart cards, and insight rows so a printed/captured tab reflows cleanly instead of cutting a card in half.

Spacing rhythm is loosely rem-based rather than a strict 4px/8px grid: tight internal gaps (0.35–0.6rem) inside compact rows (insight icon-to-text, sidebar action stack), medium gaps (1rem) for card padding and chart grids, and large gaps (1.75–2.5rem) for section separation and sidebar/drawer padding. The KPI grid uses Flexbox (`flex: 1 1 220px` per card) rather than CSS Grid, so a partial final row of cards stretches evenly to fill the row instead of leaving a short ragged row — this replaced an earlier `auto-fit, minmax(200px,1fr)` CSS Grid that could leave an uneven "3 then 2" last row. Chart grids remain an `auto-fit` CSS Grid (`minmax(260px,1fr)` for trend charts, `minmax(320px,1fr)` for breakdown charts), so those still reflow with content rather than breakpointing.

## Elevation & Depth

The system is flat by default: surfaces are separated by 1px hairline borders, not shadows, and the KPI grid itself is built from a 1px-gap background grid (cards sit in a shared hairline lattice, not as individually shadowed floating tiles). Shadow tokens exist (`--shadow-sm/md/lg`) but are used sparingly — the KPI detail flyout is the one "raised sheet" moment, using `--shadow-lg` plus the raised-panel surface color to read as a panel lifted out of the flat grid when a KPI is expanded.

### Shadow Vocabulary
- **shadow-sm** (`0 1px 2px rgba(10,12,16,0.05)` light / `rgba(0,0,0,0.4)` dark): defined but not used at rest anywhere in the shipped UI.
- **shadow-lg** (`0 12px 32px rgba(10,12,16,0.12)` light / `rgba(0,0,0,0.55)` dark): the KPI detail panel only — the single deliberate elevation moment in the system.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat and hairline-bordered at rest. The one shadow that ships (`--shadow-lg` on the KPI detail flyout) marks the one panel that is genuinely a layer above the grid, not a decorative default.

## Shapes

Radii are deliberately tight — 5px (`--radius-sm`, nav links, tabs' count badges, badges, inputs, close button), 8px (`--radius-md`, KPI grid, chart cards, insight list), 10px (`--radius-lg`, the KPI detail flyout) — to read as an instrument panel rather than a soft consumer app. No pill shapes, no large-radius cards. Borders are 1px hairlines everywhere except the dashed 1px rules that bracket the KPI explanation block, the tab bar's 1px baseline rule with a 2px signal-cyan underline on the active tab, and the query input's focus ring, which is a 3px `accent-soft` glow rather than a border-width change.

## Components

### Buttons
- **Shape:** 5px radius (`--radius-sm`) on every button variant.
- **Primary ("Ask" query submit):** signal-cyan background, panel-colored text, `0.65rem 1.2rem` padding.
- **Hover / Focus:** primary darkens to `signal-cyan-strong` and lifts `translateY(-1px)`; text inputs get a `0 0 0 3px accent-soft` focus ring instead of a border-color-only change.
- **Ghost (report-download link, sidebar action links):** panel-raised or transparent background, hairline-strong border, hover shifts border to signal-cyan plus a 1px lift.

### Cards / Containers
- **KPI card:** no individual border or shadow — cards are cells in a shared 1px-hairline Flexbox row (`flex: 1 1 220px`; the row's own background shows through the 1px gaps as rule lines). 8px radius on the row container only, not per-cell. Hover swaps the cell to the raised-panel color.
- **Chart card:** 8px radius, 1px hairline border, panel background, `1rem 1.1rem 0.6rem` padding — the one component that does carry its own border, since charts aren't gridded together. The plotted chart body sits in a height-capped wrapper (`max-height: 320px`; actual height `Math.min(320, Math.max(120, points.length * 32))`) so a chart with many category rows never grows unbounded.
- **KPI detail flyout:** 10px radius, hairline-strong border, raised-panel background, `--shadow-lg` — the system's one lifted surface.

### Inputs / Fields
- **Style:** hairline-strong 1px border, panel background, 5px radius, `0.65rem 0.9rem` padding.
- **Focus:** border shifts to signal-cyan plus a 3px `accent-soft` glow ring — no border-width change.

### Navigation
- **Tab bar (primary navigation, added 2026-09-17):** a `role="tablist"` row of Geist Sans, 600-weight tab labels, muted-ink default, full-ink on hover, signal-cyan 2px underline plus full-ink text when active. Each tab carries a mono, tabular-nums count badge (hairline background at rest, signal-cyan-soft/signal-cyan when the tab is active, danger-soft/danger when the tab is Insights and at least one insight is `critical`). Keyboard support is arrow-key/Home/End with roving `tabindex`, per the ARIA tabs pattern. This is now the dashboard's only section-level navigation.
- **Sidebar action links:** Geist Sans body text, muted-ink default, hairline background on hover — these are action buttons/links (Refresh now, Ask the dashboard toggle, PDF export), not section navigation; they carry no "active" state.

### Sidebar Schematic Connector (retired 2026-09-17)
Previously the defining custom component: a 1px hairline-strong vertical line ran behind a nav-link stack, with a 7px filled dot per link, the active section's dot filling solid signal-cyan with a glow ring. This was removed when the page moved from a single scrolling view to tabs — there is no longer a "section currently in view" for a scroll-spy connector to track. It is recorded here as a defunct pattern, not a rule for new surfaces: don't reintroduce a scroll-spy connector nav alongside the tab bar.

### Insight List Item
Each insight is a row in a bordered, hairline-divided list (not individually bordered per row — only interior `border-top` dividers between siblings). Severity is marked by a monospace bracket tag prefix — `[i]` in signal-cyan for info, `[!]` in warning-amber for warning, `[x]` in danger-red for critical — rather than a colored left border. This tag-based marking replaced an earlier colored-left-border treatment during an earlier build; the border-left approach is confirmed removed from the shipped CSS. Insights are now reached via the Insights tab rather than by scrolling to the bottom of the page.

### KPI Explanation / Formula Block
A dashed-rule "ledger" framing: an uppercase, signal-cyan, mono "Formula" label sits above the explanation text, and the explanation paragraph itself (mono, muted-ink) is bracketed top and bottom by a 1px dashed hairline-strong rule rather than a tinted, left-bordered callout box. This is the component that carries the product's "every number traces to a formula" promise, and it deliberately avoids the tinted-callout / colored-side-tab pattern used elsewhere for insights before this build's revision.

### Close Button
A 1.85rem square, 5px-radius, hairline-background glyph button (`×` character, not an icon-set glyph) used identically for the KPI detail panel and the ask drawer. Opacity steps from 0.7 to 1 and background steps to hairline-strong on hover — no color change, no border.

## Do's and Don'ts

### Do:
- **Do** set every KPI value, chart tick/tooltip, comparison percentage, tab count, and timestamp in IBM Plex Mono with tabular-nums; set everything else in Geist Sans.
- **Do** reserve signal-cyan for live/active state only (tabs, nav, focus, formula label) — never repurpose it as a fourth status color.
- **Do** separate cards and grid cells with 1px hairlines and shared-gap grids rather than individual shadows; reserve `--shadow-lg` for the one genuinely lifted surface (the KPI detail flyout).
- **Do** use monospace bracket tags (`[i]`/`[!]`/`[x]`) for insight severity and dashed-rule ledger framing for formula/explanation content.
- **Do** bound any variable-height list or chart (`max-height` + internal scroll, or a capped pixel formula) rather than letting a tab panel grow into an unbounded page — this is what keeps a printed/captured view from slicing a card across a page break.

### Don't:
- **Don't** add colored left-border "side-tab" accents to cards, list items, or callouts — this system replaced that exact pattern (insight rows, the explanation block, query-history turns) with bracket tags and dashed rules; do not reintroduce it on new surfaces.
- **Don't** use hard offset/neobrutalist shadows anywhere in this system — the shadow vocabulary is soft and blurred, and used sparingly.
- **Don't** apply the "§ Overview" mono section-label kicker uniformly above every heading — it currently marks only the Overview section; don't promote it into a system-wide repeated-kicker rule that isn't yet how the build actually uses it. **Known drift (not repaired):** the shipped CSS applies the same `::before { content: "§ " }` kicker to every `.sectionLabel` instance, so all four tab panels ("§ KPIs", "§ Monthly trends", "§ Category breakdowns", "§ Insights") currently render the kicker, not only Overview — the recorded rule and the build already disagree; flagged here rather than either silently repaired in code or promoted into a system-wide kicker rule.
- **Don't** reintroduce a scroll-spy sidebar nav (connector line + section dots) now that content is tabbed — it has no scrolling page left to track; use the tab bar for section navigation instead.

---
version: 1
slug: "frontend-src-app-page-tsx"
primary_target: "frontend/src/app/page.tsx"
related_targets: ["frontend/src/app/landing.module.css"]
---

# Landing / launch screen — surface brief

Scope: `frontend/src/app/page.tsx` (root route `/`), styled by `frontend/src/app/landing.module.css`. Mode: Persuade (a tool's landing page — even though it triggers a real backend run).

Audience/job: an academic evaluator or technical visitor, in one sitting, deciding "is this a real working multi-agent pipeline?" Action/task: pick a business domain (e-commerce/banking), trigger the real pipeline run, watch it execute, land on the generated dashboard. Proof/content: the five real agent stages (Data Engineering, KPI/Semantic, BI Analyst, Dashboard Generator, Auditor/XAI) and their live status as the actual orchestrator runs — no invented claims, no fabricated metrics.

Constraints: preserve the domain-select → run → auto-redirect-on-success interaction model, the `usePipelineRun` state machine and its stage data, the aria-live progress announcement, and reduced-motion support. Full creative freedom on visual structure/identity otherwise (confirmed by user) — this may diverge from the dashboard's "Audit Console" system; the dashboard's DESIGN.md is not binding on this surface.

## Direction contract

THESIS: This screen is a live mission-control console monitoring five subsystems (the agents), not a marketing hero with a diagram bolted on — it proves the pipeline is real by putting the visitor at the console during an actual run, not describing it. Refuses the category default (and this app's own prior look): gradient/soft hero + a decorative node-graph illustration next to a CTA button.

OWN-WORLD: Near-black instrument-black ground (`#05070a`), phosphor/status-light palette reserved for meaning — amber-white idle, cyan-white armed/live, green confirmed, red fault — against dim steel-gray chrome and hairline dividers; monospace throughout for anything measured or logged (telemetry/timestamps/coordinates), a plain condensed sans for console labels and copy. Five subsystem panels arranged as a console bank (not a flowchart), each with a status light, a designation code, and a live one-line readout; a scrolling mission log strip anchors the bottom of the viewport. No drop shadows or soft cards — panels are recessed bezels defined by inset hairlines and a subtle inner-shadow "glass," consistent with a physical instrument panel.

STORY: Visitor lands on a console, not a page. They read "MISSION PROFILE" (domain choice presented as selecting between two profiles, e.g. `PROFILE: OLIST-COMMERCE` / `PROFILE: BERKA-BANKING`), commit with a keyed "INITIATE SEQUENCE" control, then watch the five subsystem panels arm and confirm one by one in real time with genuine status text sourced from the real pipeline stages — convincing them this is live telemetry from a real system, not a canned animation — before the console reports sequence complete and hands off to the dashboard.

FIRST VIEWPORT: Full-bleed console fills the viewport at rest: a slim top strip (wordmark-as-callsign + system clock/idle status), the five subsystem panels as a horizontal bank at mid-height (stacking vertically only below the responsive breakpoint), the mission-profile selector and INITIATE control directly beneath the bank as the primary action zone, and the scrolling mission-log strip pinned to the bottom edge as the console's continuous "proof of life." Primary action (INITIATE SEQUENCE) sits dead-center beneath the panel bank, impossible to miss.

FORM: Chosen candidate — "Mission Control Console," my own top-ranked grounded direction (kicker IMPECCABLE'S PICK; not the machine-assigned card, which was "Terminal Boot Sequence," seed key `966d077f`, assigned index 4). Honest risk carried into the build: this is the most expected "ops-room" reading for an AI-pipeline demo — legitimate and effective, but not the most surprising option on the table; commit to it with real craft (genuine status-light physics, real log content, disciplined restraint on color) rather than a shallow sci-fi skin.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance.

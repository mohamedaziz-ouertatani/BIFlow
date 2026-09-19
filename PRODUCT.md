# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primary audience is an academic evaluator (professor/reviewer) assessing BIFlow as a multi-agent BI pipeline project in a single sitting, alongside a secondary general-demo audience (analysts exploring the dashboard). Design should make the pipeline's capabilities legible fast: multi-domain support, explainability, and the insight/anomaly layer, not just raw KPI numbers.

## Product Purpose

BIFlow automates a Business Intelligence pipeline end-to-end: raw transactional data in, an explainable, interactive dashboard out. Five specialized agents (Data Engineering, KPI/Semantic, BI Analyst, Dashboard Generator, Auditor/XAI) coordinated by an Orchestrator turn a raw dataset into KPI cards, trend charts, category breakdowns, and generated insights. Success means a viewer can look at the dashboard and understand both the business state (KPIs, trends, anomalies) and that the numbers are traceable/explainable (each KPI has a formula and explanation surfaced via `/api/dashboard`'s `kpi_cards[].explanation`).

## Positioning

Unlike a single BI tool wired to one dataset, BIFlow's mechanism is domain-agnostic: the same five-agent pipeline runs against structurally different datasets (e-commerce order data, banking transaction data) by swapping domain-specific KPI/dimension definitions, and every number it shows is paired with its formula and a natural-language explanation (via the Auditor/XAI agent and the on-dashboard "Ask the dashboard" query box) rather than being a black box.

## Operating Context

- Two live business domains today: e-commerce (Olist) and banking (Berka), selected by which sample dataset the orchestrator was last run against — the dashboard renders whichever `business_domain` the current `dashboard_layout.json` reports.
- Data refreshes by polling `/api/dashboard` every 5s; the dashboard has no manual refresh action.
- A PDF export of the current dashboard state exists (`/api/report.pdf`).
- A natural-language Q&A box ("Ask the dashboard") lets a viewer ask free-text questions answered by a local LLM grounded in the current dashboard context.
- KPI cards expand into a detail panel with the KPI's trend chart, formula/explanation, and related insights.

## Capabilities and Constraints

- Frontend is Next.js (App Router) + CSS Modules + Recharts, polling a FastAPI JSON API — no server-rendering of live data, everything is client-fetched.
- No user accounts/auth; the dashboard is read-only (aside from the query box and PDF export).
- No dataset-switching control in the UI yet — domain is fixed by whichever pipeline run produced the current `dashboard_layout.json`.
- Chart data available: per-metric monthly time series, and per-KPI category breakdowns (e.g. revenue by category/state for e-commerce, by region for banking, by contract/internet service for telco), capped at 8 categories + "Other".

## Brand Commitments

None. No existing logo or locked brand system — "BIFlow" is used as a plain wordmark; a full redesign is free to establish colors, typography, and visual identity from scratch.

## Evidence on Hand

No real screenshots, testimonials, or case studies on hand. The only evidence is the current running implementation (adaptive light/dark theme, fixed left sidebar with scroll-spy nav, collapsible right "ask" drawer, stat-tile KPI cards, line/bar charts) — treated as anti-reference for this redesign per the user's direction, not as a constraint.

## Product Principles

- Explainability is not an afterthought: every number should feel traceable back to a formula and a plain-language reason, not just displayed.
- Multi-domain by construction: nothing in the visual design should hard-code e-commerce- or banking-specific assumptions (icons, colors implying one domain) since the same shell renders either.
- Built to be understood fast by someone seeing it for the first time (an evaluator), not just by a returning daily user.
- Insights and anomalies are first-class, not a footnote — they're the payoff of the "multi-agent" pitch and should read as considered, not bolted on.

## Accessibility & Inclusion

No project-specific requirement established beyond general web accessibility (the current implementation uses semantic HTML and adequate contrast, but no formal standard was mandated).

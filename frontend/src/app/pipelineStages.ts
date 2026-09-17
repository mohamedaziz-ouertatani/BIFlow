// Matches the business_domain values agents/*_agent code and the backend
// API's ?domain= query param use, so the id can be passed straight through.
export type DomainId = "e-commerce" | "banking" | "telco";

export interface Domain {
  id: DomainId;
  label: string;
  sublabel: string;
  color: string;
}

export const DOMAINS: Domain[] = [
  { id: "e-commerce", label: "Olist", sublabel: "E-commerce", color: "#0891a8" },
  { id: "banking", label: "Berka", sublabel: "Banking", color: "#a3690a" },
  { id: "telco", label: "Telco", sublabel: "Subscription", color: "#7a4fa3" },
];

// Matches the real stage names orchestrator/orchestrator.py's _run_stage calls
// use (and therefore the "stage" field on /api/pipeline/run's SSE events) —
// "orchestrator" isn't one of them; it's a synthetic dispatch phase the
// frontend shows before the first real stage event arrives.
export type AgentId =
  | "orchestrator"
  | "data_engineering"
  | "kpi_semantic"
  | "bi_analyst"
  | "dashboard"
  | "auditor";

export interface AgentNode {
  id: AgentId;
  label: string;
  labelLines: string[];
  x: number;
  y: number;
  radius: number;
}

export const GRAPH_VIEWBOX = { width: 600, height: 500 };

// Orchestrator sits at the hub; the five agents (agents/*_agent) ring it in
// the execution order the orchestrator actually runs them in.
export const AGENT_NODES: AgentNode[] = [
  { id: "orchestrator", label: "BI Orchestrator", labelLines: ["BI Orchestrator"], x: 300, y: 240, radius: 46 },
  { id: "data_engineering", label: "Data Engineering (Profiling + ETL)", labelLines: ["Data Engineering"], x: 300, y: 50, radius: 34 },
  { id: "kpi_semantic", label: "KPI & Semantic", labelLines: ["KPI &", "Semantic"], x: 481, y: 181, radius: 34 },
  { id: "bi_analyst", label: "BI Analyst", labelLines: ["BI Analyst"], x: 412, y: 394, radius: 34 },
  { id: "dashboard", label: "Dashboard Generator", labelLines: ["Dashboard", "Generator"], x: 188, y: 394, radius: 34 },
  { id: "auditor", label: "BI Auditor / XAI", labelLines: ["BI Auditor", "/ XAI"], x: 119, y: 181, radius: 34 },
];

// Status labels shown under each node while it runs/finishes/errors. Keyed by
// agent id so real backend events ("stage_started" for "kpi_semantic", etc.)
// map straight onto a label without any timeline/duration bookkeeping.
export const STAGE_LABELS: Record<AgentId, { active: string; done: string; error: string }> = {
  orchestrator: { active: "Dispatching run...", done: "✓ Dispatched", error: "✗ Dispatch failed" },
  data_engineering: {
    active: "Profiling & cleaning data...",
    done: "✓ Validated",
    error: "✗ Failed",
  },
  kpi_semantic: { active: "Computing KPIs...", done: "✓ Modeled", error: "✗ Failed" },
  bi_analyst: { active: "Analyzing trends...", done: "✓ Analyzed", error: "✗ Failed" },
  dashboard: { active: "Building dashboard...", done: "✓ Rendered", error: "✗ Failed" },
  auditor: { active: "Auditing findings...", done: "✓ Audited", error: "✗ Failed" },
};

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

// Mirrors the real stage names the orchestrator logs in
// orchestrator/orchestrator.py (_run_stage calls), so this timeline can later
// be driven by actual pipeline events instead of a fixed schedule.
export type AgentId =
  | "orchestrator"
  | "data_engineering"
  | "kpi_semantic"
  | "bi_analyst"
  | "dashboard"
  | "audit";

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
  { id: "audit", label: "BI Auditor / XAI", labelLines: ["BI Auditor", "/ XAI"], x: 119, y: 181, radius: 34 },
];

export interface PipelineStage {
  agent: AgentId;
  runningLabel: string;
  doneLabel: string;
  durationMs: number;
}

// Reusable, inspectable timeline: swap durations/labels here, or later drive
// this array from real backend pipeline events instead of a fixed schedule.
export const PIPELINE_STAGES: PipelineStage[] = [
  {
    agent: "orchestrator",
    runningLabel: "Dispatching run...",
    doneLabel: "✓ Dispatched",
    durationMs: 450,
  },
  {
    agent: "data_engineering",
    runningLabel: "Profiling & cleaning data...",
    doneLabel: "✓ Validated",
    durationMs: 750,
  },
  {
    agent: "kpi_semantic",
    runningLabel: "Computing KPIs...",
    doneLabel: "✓ Modeled",
    durationMs: 700,
  },
  {
    agent: "bi_analyst",
    runningLabel: "Analyzing trends...",
    doneLabel: "✓ Analyzed",
    durationMs: 700,
  },
  {
    agent: "dashboard",
    runningLabel: "Building dashboard...",
    doneLabel: "✓ Rendered",
    durationMs: 650,
  },
  {
    agent: "audit",
    runningLabel: "Auditing findings...",
    doneLabel: "✓ Audited",
    durationMs: 650,
  },
];

export const TOTAL_PIPELINE_DURATION_MS = PIPELINE_STAGES.reduce(
  (sum, stage) => sum + stage.durationMs,
  0
);

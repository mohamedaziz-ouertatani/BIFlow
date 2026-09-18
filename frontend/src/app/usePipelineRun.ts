"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AGENT_NODES, STAGE_LABELS, type AgentId } from "./pipelineStages";

export type StageStatus = "idle" | "active" | "done" | "error";

export interface LogEntry {
  id: string;
  time: number;
  text: string;
}

export interface PipelineRunState {
  status: "idle" | "running" | "succeeded" | "failed";
  stages: Record<AgentId, StageStatus>;
  error: string | null;
  log: LogEntry[];
}

interface PipelineEvent {
  type:
    | "stage_started"
    | "stage_succeeded"
    | "stage_failed"
    | "pipeline_succeeded"
    | "pipeline_failed";
  stage?: AgentId;
  error?: string;
}

const IDLE_STAGES = Object.fromEntries(
  AGENT_NODES.map((node) => [node.id, "idle"])
) as Record<AgentId, StageStatus>;

const INITIAL_STATE: PipelineRunState = { status: "idle", stages: IDLE_STAGES, error: null, log: [] };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let logSeq = 0;
function nodeLabel(stage: AgentId): string {
  return AGENT_NODES.find((node) => node.id === stage)!.label;
}
function logEntry(text: string): LogEntry {
  logSeq += 1;
  return { id: `log-${logSeq}`, time: Date.now(), text };
}

// Drives the landing page's mission console from the real orchestrator run
// (GET /api/pipeline/run, Server-Sent Events) instead of a fixed timeline:
// each subsystem panel and log line reflects exactly what the backend reports.
export function usePipelineRun() {
  const [state, setState] = useState<PipelineRunState>(INITIAL_STATE);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => sourceRef.current?.close();
  }, []);

  const run = useCallback((domain: string) => {
    sourceRef.current?.close();
    setState({
      status: "running",
      stages: { ...IDLE_STAGES, orchestrator: "active" },
      error: null,
      log: [logEntry(`${nodeLabel("orchestrator")} — ${STAGE_LABELS.orchestrator.active}`)],
    });

    const source = new EventSource(
      `${API_URL}/api/pipeline/run?domain=${encodeURIComponent(domain)}`
    );
    sourceRef.current = source;

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as PipelineEvent;

      setState((prev) => {
        switch (payload.type) {
          case "stage_started": {
            const stage = payload.stage as AgentId;
            return {
              ...prev,
              stages: { ...prev.stages, orchestrator: "done", [stage]: "active" },
              log: [...prev.log, logEntry(`${nodeLabel(stage)} — ${STAGE_LABELS[stage].active}`)],
            };
          }
          case "stage_succeeded": {
            const stage = payload.stage as AgentId;
            return {
              ...prev,
              stages: { ...prev.stages, [stage]: "done" },
              log: [...prev.log, logEntry(`${nodeLabel(stage)} — ${STAGE_LABELS[stage].done}`)],
            };
          }
          case "stage_failed": {
            const stage = payload.stage as AgentId;
            return {
              ...prev,
              stages: { ...prev.stages, [stage]: "error" },
              log: [...prev.log, logEntry(`${nodeLabel(stage)} — ${STAGE_LABELS[stage].error}`)],
            };
          }
          case "pipeline_succeeded":
            source.close();
            return {
              ...prev,
              status: "succeeded",
              log: [...prev.log, logEntry("Sequence complete — handing off to dashboard.")],
            };
          case "pipeline_failed":
            source.close();
            return {
              ...prev,
              status: "failed",
              error: payload.error ?? "The pipeline failed.",
              log: [...prev.log, logEntry(`Sequence aborted — ${payload.error ?? "unknown error"}`)],
            };
          default:
            return prev;
        }
      });
    };

    source.onerror = () => {
      source.close();
      setState((prev) =>
        prev.status === "running"
          ? {
              ...prev,
              status: "failed",
              error: "Lost connection to the pipeline.",
              log: [...prev.log, logEntry("Sequence aborted — lost connection to the pipeline.")],
            }
          : prev
      );
    };
  }, []);

  const reset = useCallback(() => {
    sourceRef.current?.close();
    setState(INITIAL_STATE);
  }, []);

  return { state, run, reset };
}

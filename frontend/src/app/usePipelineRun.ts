"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AGENT_NODES, type AgentId } from "./pipelineStages";

export type StageStatus = "idle" | "active" | "done" | "error";

export interface PipelineRunState {
  status: "idle" | "running" | "succeeded" | "failed";
  stages: Record<AgentId, StageStatus>;
  error: string | null;
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

const INITIAL_STATE: PipelineRunState = { status: "idle", stages: IDLE_STAGES, error: null };

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Drives the landing page's pipeline animation from the real orchestrator run
// (GET /api/pipeline/run, Server-Sent Events) instead of a fixed timeline:
// each stage lights up and completes exactly when the backend says it did.
export function usePipelineRun() {
  const [state, setState] = useState<PipelineRunState>(INITIAL_STATE);
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    return () => sourceRef.current?.close();
  }, []);

  const run = useCallback((domain: string) => {
    sourceRef.current?.close();
    setState({ status: "running", stages: { ...IDLE_STAGES, orchestrator: "active" }, error: null });

    const source = new EventSource(
      `${API_URL}/api/pipeline/run?domain=${encodeURIComponent(domain)}`
    );
    sourceRef.current = source;

    source.onmessage = (event) => {
      const payload = JSON.parse(event.data) as PipelineEvent;

      setState((prev) => {
        switch (payload.type) {
          case "stage_started":
            return {
              ...prev,
              stages: {
                ...prev.stages,
                orchestrator: "done",
                [payload.stage as AgentId]: "active",
              },
            };
          case "stage_succeeded":
            return { ...prev, stages: { ...prev.stages, [payload.stage as AgentId]: "done" } };
          case "stage_failed":
            return { ...prev, stages: { ...prev.stages, [payload.stage as AgentId]: "error" } };
          case "pipeline_succeeded":
            source.close();
            return { ...prev, status: "succeeded" };
          case "pipeline_failed":
            source.close();
            return { ...prev, status: "failed", error: payload.error ?? "The pipeline failed." };
          default:
            return prev;
        }
      });
    };

    source.onerror = () => {
      source.close();
      setState((prev) =>
        prev.status === "running"
          ? { ...prev, status: "failed", error: "Lost connection to the pipeline." }
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

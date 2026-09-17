"use client";

import { AGENT_NODES, GRAPH_VIEWBOX, PIPELINE_STAGES, type AgentId } from "./pipelineStages";
import styles from "./landing.module.css";

export type AgentStatus = "idle" | "active" | "done";

const orchestrator = AGENT_NODES.find((node) => node.id === "orchestrator")!;
const spokes = AGENT_NODES.filter((node) => node.id !== "orchestrator");

// Derives a node's run status from its position in PIPELINE_STAGES relative to
// the stage currently playing, so the graph stays in sync with a single index.
function statusFor(agent: AgentId, activeIndex: number): AgentStatus {
  const stageIndex = PIPELINE_STAGES.findIndex((stage) => stage.agent === agent);
  if (stageIndex === -1 || activeIndex < 0) return "idle";
  if (stageIndex < activeIndex) return "done";
  if (stageIndex === activeIndex) return "active";
  return "idle";
}

function statusLabelFor(agent: AgentId, status: AgentStatus): string | null {
  if (status === "idle") return null;
  const stage = PIPELINE_STAGES.find((s) => s.agent === agent);
  if (!stage) return null;
  return status === "active" ? stage.runningLabel : stage.doneLabel;
}

export default function PipelineGraph({ activeIndex }: { activeIndex: number }) {
  return (
    <svg
      viewBox={`0 0 ${GRAPH_VIEWBOX.width} ${GRAPH_VIEWBOX.height}`}
      className={styles.graphSvg}
      role="img"
      aria-label="Multi-agent pipeline graph"
    >
      {spokes.map((node) => {
        const status = statusFor(node.id, activeIndex);
        return (
          <line
            key={`edge-${node.id}`}
            x1={orchestrator.x}
            y1={orchestrator.y}
            x2={node.x}
            y2={node.y}
            className={`${styles.edge} ${status !== "idle" ? styles.edgeActive : ""}`}
          />
        );
      })}

      {spokes.map((node) => {
        if (statusFor(node.id, activeIndex) !== "active") return null;
        const stage = PIPELINE_STAGES.find((s) => s.agent === node.id);
        return (
          <circle key={`dot-${node.id}-${activeIndex}`} r={5} className={styles.travelingDot}>
            <animateMotion
              dur={`${(stage?.durationMs ?? 600) / 1000}s`}
              repeatCount="indefinite"
              path={`M${orchestrator.x},${orchestrator.y} L${node.x},${node.y}`}
            />
          </circle>
        );
      })}

      {AGENT_NODES.map((node) => {
        const status = statusFor(node.id, activeIndex);
        const isHub = node.id === "orchestrator";
        const statusLabel = statusLabelFor(node.id, status);
        const labelStartY = node.radius + 20;

        return (
          <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
            <circle
              r={node.radius}
              className={`${styles.node} ${isHub ? styles.hubNode : ""} ${styles[`node-${status}`]}`}
            />
            <text className={styles.nodeLabel} textAnchor="middle" dy={isHub ? 5 : 4}>
              {node.labelLines.map((line, i) => (
                <tspan key={line} x={0} dy={i === 0 ? (isHub ? 0 : -6) : 13}>
                  {line}
                </tspan>
              ))}
            </text>
            {statusLabel && (
              <text
                y={labelStartY}
                textAnchor="middle"
                className={`${styles.statusLabel} ${styles[`statusLabel-${status}`]}`}
              >
                {statusLabel}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

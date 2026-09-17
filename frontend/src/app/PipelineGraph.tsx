"use client";

import { AGENT_NODES, GRAPH_VIEWBOX, STAGE_LABELS, type AgentId } from "./pipelineStages";
import type { StageStatus } from "./usePipelineRun";
import styles from "./landing.module.css";

const orchestrator = AGENT_NODES.find((node) => node.id === "orchestrator")!;
const spokes = AGENT_NODES.filter((node) => node.id !== "orchestrator");

function statusLabelFor(agent: AgentId, status: StageStatus): string | null {
  if (status === "idle") return null;
  return STAGE_LABELS[agent][status];
}

export default function PipelineGraph({ stages }: { stages: Record<AgentId, StageStatus> }) {
  return (
    <svg
      viewBox={`0 0 ${GRAPH_VIEWBOX.width} ${GRAPH_VIEWBOX.height}`}
      className={styles.graphSvg}
      role="img"
      aria-label="Multi-agent pipeline graph"
    >
      {spokes.map((node) => {
        const status = stages[node.id];
        return (
          <line
            key={`edge-${node.id}`}
            x1={orchestrator.x}
            y1={orchestrator.y}
            x2={node.x}
            y2={node.y}
            className={`${styles.edge} ${status !== "idle" ? styles.edgeActive : ""} ${
              status === "error" ? styles.edgeError : ""
            }`}
          />
        );
      })}

      {spokes.map((node) => {
        if (stages[node.id] !== "active") return null;
        return (
          <circle key={`dot-${node.id}`} r={5} className={styles.travelingDot}>
            <animateMotion
              dur="0.9s"
              repeatCount="indefinite"
              path={`M${orchestrator.x},${orchestrator.y} L${node.x},${node.y}`}
            />
          </circle>
        );
      })}

      {AGENT_NODES.map((node) => {
        const status = stages[node.id];
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

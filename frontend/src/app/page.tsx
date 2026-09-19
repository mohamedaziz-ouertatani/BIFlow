"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import styles from "./landing.module.css";
import { AGENT_NODES, DOMAINS, STAGE_LABELS, type AgentId, type DomainId } from "./pipelineStages";
import { usePipelineRun, type PipelineRunState, type StageStatus } from "./usePipelineRun";

const SUBSYSTEMS = AGENT_NODES.filter((node) => node.id !== "orchestrator");

const PANEL_CODE: Record<AgentId, string> = {
  orchestrator: "SYS·00",
  data_engineering: "SYS·01",
  kpi_semantic: "SYS·02",
  bi_analyst: "SYS·03",
  dashboard: "SYS·04",
  auditor: "SYS·05",
};

function readoutFor(agent: AgentId, status: StageStatus): string {
  if (status === "idle") return "Standing by";
  return STAGE_LABELS[agent][status];
}

// Text for the aria-live region: gives screen-reader/keyboard users the same
// progress signal sighted users get from the console's status lights and log.
function announcementFor(state: PipelineRunState): string {
  if (state.status === "succeeded") return "Pipeline complete. Opening dashboard.";
  if (state.status === "failed") return state.error ?? "Pipeline failed.";
  const activeNode = AGENT_NODES.find((node) => state.stages[node.id] === "active");
  return activeNode ? `${activeNode.label}: ${STAGE_LABELS[activeNode.id].active}` : "";
}

function formatClock(date: Date): string {
  return date.toLocaleTimeString("en-GB", { hour12: false });
}

// Landing / mission-control screen: pick a domain, arm the real pipeline for
// it, watch the five subsystems report in over the live log, then hand off
// to the dashboard once the run succeeds.
export default function LandingPage() {
  const router = useRouter();
  const [selectedDomain, setSelectedDomain] = useState<DomainId | null>(null);
  const { state, run, reset } = usePipelineRun();
  const running = state.status === "running";
  const logRef = useRef<HTMLElement | null>(null);
  const [clock, setClock] = useState<Date | null>(null);

  // The clock starts empty so server and client render the same markup, then
  // ticks from the first timer callback (setState inside a callback, not
  // synchronously in the effect body).
  useEffect(() => {
    const tick = () => setClock(new Date());
    const first = setTimeout(tick, 0);
    const id = setInterval(tick, 1000);
    return () => {
      clearTimeout(first);
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    // Keep the mission log scrolled to the newest line whenever an entry is added.
    const node = logRef.current;
    if (!node) return;
    // jsdom (the Jest test DOM) has no scrollTo, so fall back to setting scrollTop directly.
    if (typeof node.scrollTo === "function") {
      node.scrollTo({ top: node.scrollHeight, behavior: "smooth" });
    } else {
      node.scrollTop = node.scrollHeight;
    }
  }, [state.log.length]);

  useEffect(() => {
    // After a successful run, wait 500ms so 'Sequence complete' is visible, then open that domain's
    // dashboard. The cleanup cancels the timer if the state changes before it fires.
    if (state.status !== "succeeded" || !selectedDomain) return;
    const timeout = setTimeout(() => {
      router.push(`/dashboard?domain=${selectedDomain}`);
    }, 500);
    return () => clearTimeout(timeout);
  }, [state.status, selectedDomain, router]);

  const handleRun = () => {
    if (!selectedDomain || running) return;
    run(selectedDomain);
  };

  const handleSelectDomain = (id: DomainId) => {
    if (running) return;
    setSelectedDomain(id);
    // Switching domains after a finished/failed run should show a clean
    // console, not the previous domain's leftover done/error panels.
    if (state.status !== "idle") reset();
  };

  const systemState = running
    ? "armed"
    : state.status === "succeeded"
    ? "done"
    : state.status === "failed"
    ? "error"
    : "idle";

  const systemText = running
    ? STAGE_LABELS.orchestrator.active
    : state.status === "succeeded"
    ? "Sequence complete"
    : state.status === "failed"
    ? "Sequence aborted"
    : "Standing by";

  return (
    <div className={styles.shell}>
      <div className={styles.scanlines} aria-hidden="true" />

      <header className={styles.consoleHeader}>
        <div className={styles.callsign}>
          <span className={styles.callsignMark} aria-hidden="true">
            ◆
          </span>
          BIFLOW
          <span className={styles.callsignSuffix}>{"// OPS CONSOLE"}</span>
        </div>
        <div className={styles.systemStatus}>
          <span className={`${styles.statusDot} ${styles[`statusDot-${systemState}`]}`} />
          <span className={styles.statusText}>{systemText}</span>
          <span className={styles.clock}>{clock ? formatClock(clock) : "--:--:--"}</span>
        </div>
      </header>

      <div aria-live="polite" className={styles.srOnly}>
        {announcementFor(state)}
      </div>

      <main className={styles.main}>
        <div className={styles.panelBank}>
          {SUBSYSTEMS.map((node) => {
            const status = state.stages[node.id];
            return (
              <div key={node.id} className={`${styles.panel} ${styles[`panel-${status}`]}`}>
                <div className={styles.panelHeader}>
                  <span className={styles.panelLight} />
                  <span className={styles.panelCode}>{PANEL_CODE[node.id]}</span>
                </div>
                <p className={styles.panelTitle}>{node.labelLines.join(" ")}</p>
                <p className={styles.panelReadout}>{readoutFor(node.id, status)}</p>
              </div>
            );
          })}
        </div>

        <div className={styles.controlDeck}>
          <p className={styles.deckLabel}>Mission profile</p>
          <div className={styles.profileGrid}>
            {DOMAINS.map((domain) => (
              <button
                key={domain.id}
                type="button"
                disabled={running}
                className={`${styles.profileCard} ${
                  selectedDomain === domain.id ? styles.profileSelected : ""
                }`}
                style={{ "--profile-color": domain.color } as React.CSSProperties}
                aria-pressed={selectedDomain === domain.id}
                onClick={() => handleSelectDomain(domain.id)}
              >
                <span className={styles.profileDot} />
                <span className={styles.profileText}>
                  <span className={styles.profileName}>{domain.label}</span>
                  <span className={styles.profileSub}>{domain.sublabel}</span>
                </span>
              </button>
            ))}
          </div>

          <button
            type="button"
            className={styles.initiateButton}
            disabled={!selectedDomain || running}
            onClick={handleRun}
          >
            {running
              ? "Running pipeline…"
              : state.status === "failed"
              ? "Retry Pipeline"
              : "Run Pipeline"}
          </button>

          {!selectedDomain && state.status === "idle" && (
            <p className={styles.hint}>Choose a domain to enable the run.</p>
          )}
          {state.status === "failed" && <p className={styles.errorHint}>{state.error}</p>}
        </div>
      </main>

      <footer className={styles.missionLog} ref={logRef}>
        {state.log.length === 0 ? (
          <p className={styles.logIdle}>Awaiting sequence initiation…</p>
        ) : (
          state.log.map((entry) => (
            <p key={entry.id} className={styles.logLine}>
              <span className={styles.logTime}>
                [{new Date(entry.time).toLocaleTimeString("en-GB", { hour12: false })}]
              </span>{" "}
              {entry.text}
            </p>
          ))
        )}
      </footer>
    </div>
  );
}

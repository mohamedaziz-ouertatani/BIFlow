"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import PipelineGraph from "./PipelineGraph";
import styles from "./landing.module.css";
import { DOMAINS, type DomainId } from "./pipelineStages";
import { usePipelineRun } from "./usePipelineRun";

// Landing / control-panel screen: pick a domain, run the real pipeline for
// it, then hand off to the dashboard once the run succeeds.
export default function LandingPage() {
  const router = useRouter();
  const [selectedDomain, setSelectedDomain] = useState<DomainId | null>(null);
  const { state, run, reset } = usePipelineRun();
  const running = state.status === "running";

  useEffect(() => {
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
    // Switching domains after a finished/failed run should show a clean graph,
    // not the previous domain's leftover done/error nodes.
    if (state.status !== "idle") reset();
  };

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <div className={styles.wordmark}>BIFlow</div>
        <p className={styles.tagline}>
          Automated BI pipeline powered by 5 collaborative agents
        </p>
      </header>

      <div className={styles.main}>
        <div className={styles.graphCard}>
          <PipelineGraph stages={state.stages} />
        </div>

        <div className={styles.controls}>
          <p className={styles.sectionLabel}>Select a domain</p>
          <div className={styles.domainGrid}>
            {DOMAINS.map((domain) => (
              <button
                key={domain.id}
                type="button"
                disabled={running}
                className={`${styles.domainCard} ${
                  selectedDomain === domain.id ? styles.domainSelected : ""
                }`}
                style={{ "--domain-color": domain.color } as React.CSSProperties}
                aria-pressed={selectedDomain === domain.id}
                onClick={() => handleSelectDomain(domain.id)}
              >
                <span className={styles.domainDot} />
                <span className={styles.domainText}>
                  <span className={styles.domainName}>{domain.label}</span>
                  <span className={styles.domainSub}>{domain.sublabel}</span>
                </span>
              </button>
            ))}
          </div>

          <button
            type="button"
            className={styles.runButton}
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
          {state.status === "failed" && (
            <p className={styles.errorHint}>{state.error}</p>
          )}
        </div>
      </div>
    </div>
  );
}

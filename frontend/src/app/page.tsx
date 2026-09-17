"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import PipelineGraph from "./PipelineGraph";
import styles from "./landing.module.css";
import { DOMAINS, PIPELINE_STAGES, type DomainId } from "./pipelineStages";

// Landing / control-panel screen: pick a domain, watch the seven agents run
// in sequence, then hand off to the real dashboard for that domain.
export default function LandingPage() {
  const router = useRouter();
  const [selectedDomain, setSelectedDomain] = useState<DomainId | null>(null);
  const [running, setRunning] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const timeoutsRef = useRef<ReturnType<typeof setTimeout>[]>([]);

  useEffect(() => {
    const timeouts = timeoutsRef.current;
    return () => {
      timeouts.forEach(clearTimeout);
    };
  }, []);

  const handleRun = useCallback(() => {
    if (!selectedDomain || running) return;
    setRunning(true);
    setActiveIndex(0);

    let elapsed = 0;
    PIPELINE_STAGES.forEach((stage, i) => {
      elapsed += stage.durationMs;
      if (i === PIPELINE_STAGES.length - 1) return;
      const timeout = setTimeout(() => setActiveIndex(i + 1), elapsed);
      timeoutsRef.current.push(timeout);
    });

    const finalTimeout = setTimeout(() => {
      router.push(`/dashboard?domain=${selectedDomain}`);
    }, elapsed + 400);
    timeoutsRef.current.push(finalTimeout);
  }, [selectedDomain, running, router]);

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
          <PipelineGraph activeIndex={activeIndex} />
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
                onClick={() => setSelectedDomain(domain.id)}
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
            {running ? "Running pipeline…" : "Run Pipeline"}
          </button>

          {!selectedDomain && !running && (
            <p className={styles.hint}>Choose a domain to enable the run.</p>
          )}
        </div>
      </div>
    </div>
  );
}

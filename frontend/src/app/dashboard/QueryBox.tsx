"use client";

import { useState } from "react";
import styles from "./page.module.css";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface QueryTurn {
  question: string;
  answer: string;
}

type QueryStatus =
  | { state: "idle" }
  | { state: "loading" }
  | { state: "error"; message: string };

// Sends a question to the /api/query endpoint and returns the answer text, throwing a user-facing message on failure.
async function askQuestion(question: string, domain?: string | null): Promise<string> {
  const url = domain
    ? `${API_URL}/api/query?domain=${encodeURIComponent(domain)}`
    : `${API_URL}/api/query`;
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(body?.detail ?? `API returned ${response.status}`);
  }
  const data = (await response.json()) as { answer: string };
  return data.answer;
}

// Chat-style box: lets the user ask a question about the dashboard and shows the local LLM's answer.
export default function QueryBox({ domain }: { domain?: string | null }) {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<QueryTurn[]>([]);
  const [status, setStatus] = useState<QueryStatus>({ state: "idle" });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const question = input.trim();
    // Ignore empty input, and a second submit while a request is still in flight.
    if (!question || status.state === "loading") return;

    setStatus({ state: "loading" });
    try {
      const answer = await askQuestion(question, domain);
      setTurns((prev) => [...prev, { question, answer }]);
      setStatus({ state: "idle" });
      setInput("");
    } catch (err) {
      setStatus({
        state: "error",
        message: err instanceof Error ? err.message : "Something went wrong.",
      });
    }
  };

  return (
    <section>
      <h2 className={styles.subheading}>Ask the dashboard</h2>
      {turns.length > 0 && (
        <div className={styles.queryHistory}>
          {turns.map((turn, i) => (
            <div key={i} className={styles.queryTurn}>
              <p className={styles.queryQuestion}>{turn.question}</p>
              <p className={styles.queryAnswer}>{turn.answer}</p>
            </div>
          ))}
        </div>
      )}
      <form onSubmit={handleSubmit} className={styles.queryForm}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about this dashboard…"
          disabled={status.state === "loading"}
          className={styles.queryInput}
        />
        <button
          type="submit"
          disabled={status.state === "loading"}
          className={styles.queryButton}
        >
          {status.state === "loading" ? "Thinking…" : "Ask"}
        </button>
      </form>
      {status.state === "error" && <p className={styles.error}>{status.message}</p>}
    </section>
  );
}

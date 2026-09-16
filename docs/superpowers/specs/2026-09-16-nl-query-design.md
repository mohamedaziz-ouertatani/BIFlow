# Natural-Language Querying over the Dashboard — Design

## Purpose

Let a user type a question ("why did banking churn spike in March") into
the dashboard and get a plain-language answer grounded in the numbers the
pipeline already computed — KPIs, monthly trends/anomalies, insights. This
is a read-only Q&A surface over existing output, not a new analysis engine.

## Constraints

- No new orchestrator stage or agent. Reuses the Dashboard Agent's existing
  API process and the `dashboard_layout.json` file it already serves via
  `GET /api/dashboard`.
- LLM access is a local Ollama instance (`http://localhost:11434`), already
  running with `qwen2.5:3b` and `qwen2.5-coder:7b` installed. No Anthropic
  API key is assumed for this feature.
- Answers must be grounded only in the dashboard layout JSON already
  computed by the pipeline — no new computation, no access to raw data.
- If Ollama is unreachable, the feature must fail visibly and gracefully
  (clear error surfaced to the user), not crash the dashboard or the API.

## Architecture

```
[Frontend chat box] --POST /api/query {question}--> [Dashboard API]
                                                          |
                                          reads dashboard_layout.json
                                                          |
                                          builds compact context string
                                                          |
                                      POST http://localhost:11434/api/generate
                                                          |
                                                    <-- {answer text}
                                                          |
                        <-- {answer: string} -------------
```

### Backend: `agents/dashboard_agent/nl_query.py`

- `build_context(layout: dict) -> str` — serializes KPI cards, monthly
  trends (including `is_anomaly`/`z_score`), and insights from the layout
  JSON into a compact plain-text block for the LLM prompt. Pure function,
  easy to unit test without a network call.
- `SYSTEM_PROMPT` — instructs the model to answer only from the supplied
  context, cite the actual numbers, and say "I don't have that data" for
  anything not covered (business_domain-aware, since KPI names differ
  between e-commerce and banking).
- `generate_answer(question: str, layout: dict, client=None) -> str` —
  builds the context, POSTs to Ollama's `/api/generate` (non-streaming,
  `stream: false`) with the system+user prompt, returns `response["response"]`.
  `client` is an injected `httpx.Client`-like object (defaults to a real
  one) so tests can substitute a fake and assert no real network call
  happens.

### API: `agents/dashboard_agent/api.py`

- New `POST /api/query` route, request body `{question: str}` (Pydantic
  model), response `{answer: str}`.
- Loads the same `resolved_layout_path` used by `/api/dashboard`; 404 if it
  doesn't exist yet (same as the existing endpoint).
- Wraps the Ollama call: on connection failure, returns HTTP 503 with
  `{detail: "Local LLM unavailable — is Ollama running?"}` rather than a
  500 or a hang. A configurable timeout (default 30s) on the Ollama call
  itself, with a 504-style error message on timeout.
- `OLLAMA_MODEL` env var (default `qwen2.5:3b`), `OLLAMA_URL` env var
  (default `http://localhost:11434`) — same pattern as `ALLOWED_ORIGINS`,
  read once in `create_app` so tests can override.

### Frontend: `frontend/src/app/QueryBox.tsx`

- New component: text input + submit button + scrolling list of
  question/answer pairs + loading state + inline error state.
- Calls `POST {NEXT_PUBLIC_API_URL}/api/query`, same base URL pattern
  already used for `/api/dashboard`.
- Mounted on the existing dashboard page (`page.tsx`), below the Insights
  section.
- Loading state: disable input + show a spinner/placeholder while awaiting
  the response (calls can take several seconds on a local 3B model).
- Error state: if the fetch fails or the API returns non-200, show the
  `detail` message inline instead of a blank/broken answer.

## Data Flow / Error Handling Summary

| Failure point | Handling |
|---|---|
| No `dashboard_layout.json` yet | 404, same message as `/api/dashboard` |
| Ollama not running / connection refused | 503, `"Local LLM unavailable — is Ollama running?"` |
| Ollama call times out | 504-equivalent error with a clear message |
| Frontend fetch fails | Inline error text in the chat panel, input re-enabled |

## Testing

- `test_nl_query.py`: `build_context` output contains expected KPI/trend/
  insight text for a sample layout dict (pure function, no mocking needed).
  `generate_answer` tested with an injected fake client — asserts the
  prompt sent includes the context and question, and that the function
  returns the fake response text. A separate test asserts a connection
  error from the fake client surfaces as a specific exception the API
  layer can catch and turn into a 503.
- `test_api.py` (existing file, extended): `POST /api/query` happy path
  with a monkeypatched `generate_answer`; 404 when no layout file exists;
  503 when the LLM call raises the connection-error exception.
- Frontend: `QueryBox.test.tsx` — renders, submits, shows loading state,
  shows the answer on success (mocked `fetch`), shows the error message on
  a failed/non-200 response.

## Out of Scope

- No conversation memory across questions (each question is answered
  independently from the current layout snapshot).
- No new computation/drill-down beyond what's already in the layout JSON.
- No Anthropic/cloud LLM wiring in this pass — `LLM_PROVIDER`/
  `ANTHROPIC_API_KEY` in `.env.example` remain unused by this feature.

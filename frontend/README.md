# BIFlow Dashboard (Next.js)

The BIFlow dashboard frontend — replaces the earlier Streamlit UI. Polls
the FastAPI backend in `agents/dashboard_agent/api.py` every 5 seconds and
renders KPI cards, monthly trend charts, and a severity-colored insights
list.

## How it works

`src/app/page.tsx` is a client component (`"use client"`) that:
- Fetches `GET {NEXT_PUBLIC_API_URL}/api/dashboard` on mount and every 5s
- Renders a card per KPI (`kpi_cards`), a line chart per metric in
  `monthly_trends` (via `TrendChart.tsx`, using Recharts), and a list item
  per insight (`insights`), colored by severity (info/warning/critical)
- Handles the loading, "no data yet" (404 — pipeline hasn't run), and
  error (API unreachable) states

`NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000`. It's read
**client-side in the browser**, not inside the Docker network — so when
running via `docker-compose`, it must point at a host-reachable address
(`http://localhost:8000`, matching the `dashboard_agent` service's exposed
port), never the internal service name.

## Local dev

```bash
npm install
npm run dev
```

Requires the API running too (`uvicorn agents.dashboard_agent.api:create_app --factory`)
and the pipeline having run at least once (`python -m orchestrator data/sample/olist e-commerce`)
so there's a `dashboard_layout.json` to serve.

## Testing

```bash
npm test          # Jest + React Testing Library
npm run lint
npm run build     # also runs TypeScript's checker
```

`page.test.tsx` mocks `global.fetch` (ready/no-data/error states, plus a
fake-timers test proving the poll actually re-fires after 5s) —
`TrendChart.test.tsx` renders it with real data. Mocking `fetch` here is
standard frontend practice, not a break from this repo's "no mocks"
Python-side testing philosophy: the Python backend's real behavior
(Postgres, HTTP via `TestClient`, the full pipeline) is already covered by
`pytest`, so these tests only need to prove the *frontend* renders
correctly given a response shape — not re-prove the API works.

## Via docker-compose

```bash
docker-compose up dashboard_agent frontend
```

Frontend on `:3000`, API on `:8000`. Note: the frontend image has no
bind-mount volume (unlike the Python services), so a code change requires
`docker-compose up -d --build frontend` to take effect.

## TODO
- [x] Add a trend chart once the layout includes `AnalysisResult.trends["monthly"]`
- [x] Automated frontend tests (Jest + React Testing Library)
- [ ] End-to-end tests (Playwright) against the real API, if deeper
  coverage is ever needed beyond mocked-fetch unit tests

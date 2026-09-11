# BIFlow Dashboard (Next.js)

The BIFlow dashboard frontend — replaces the earlier Streamlit UI. Polls
the FastAPI backend in `agents/dashboard_agent/api.py` every 5 seconds and
renders KPI cards plus a severity-colored insights list.

## How it works

`src/app/page.tsx` is a client component (`"use client"`) that:
- Fetches `GET {NEXT_PUBLIC_API_URL}/api/dashboard` on mount and every 5s
- Renders a card per KPI (`kpi_cards`) and a list item per insight
  (`insights`), colored by severity (info/warning/critical)
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

## Via docker-compose

```bash
docker-compose up dashboard_agent frontend
```

Frontend on `:3000`, API on `:8000`.

## TODO
- [ ] Add a trend chart once the layout includes `AnalysisResult.trends["monthly"]`
  (see `agents/dashboard_agent/README.md`)
- [ ] Automated frontend tests (currently verified manually via browser +
  the backend's own `pytest` suite — no Jest/Playwright yet)

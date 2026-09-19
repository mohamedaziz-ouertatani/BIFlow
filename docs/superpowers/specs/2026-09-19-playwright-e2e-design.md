# Playwright end-to-end tests — design

## Goal

Prove the real system works from the browser: the landing console runs the
real pipeline, and the dashboard renders, drills down, exports and answers
questions from what that run produced. The Jest tests cannot show this
because they mock `fetch`; the pytest suite cannot because it never opens a
browser.

## Non-goals

- A test per business domain. Domain behaviour is covered by pytest.
- Visual/snapshot tests. The design is still moving; they would be brittle.
- Testing Ollama. The Ask box's network response is stubbed.
- Running against the Docker stack or the full Olist/Berka datasets.

## Approach

Run against the **committed sample data** (`data/sample/`), not the gitignored
full datasets. The sample run takes seconds, is deterministic (the sample is
seeded) and works in CI. It exercises the same code path as a full run.

### The one production-code change

`DOMAIN_DATASETS` in `agents/dashboard_agent/api.py` hardcodes `data/raw/...`
paths for live-triggered runs. Add an env var `BIFLOW_DATASET_SET`:

- unset or `raw` — today's behaviour, unchanged.
- `sample` — use `data/sample/olist`, `data/sample/banking`,
  `data/sample/telco` (note the directory names differ from raw: `berka` vs
  `banking`, so this is a second mapping, not just a different root).

An unknown value raises at startup rather than silently falling back. Covered
by a pytest test on the resolver.

Everything else the harness needs is already configurable by env:
`DASHBOARD_LAYOUT_PATH`, `ANALYTICAL_TABLE_PATH`, `ALLOWED_ORIGINS`. The
frontend reads `NEXT_PUBLIC_API_URL` at **build** time, so it must be set when
the frontend is built.

## Harness

New in `frontend/`: `playwright.config.ts`, `e2e/` (specs and a small helper),
`npm run e2e`, dev dependency `@playwright/test`. Chromium only.

`webServer` starts two processes (both `reuseExistingServer: false`, so a
stray local stack can't be silently tested):

| Server | Command (cwd) | Port |
|---|---|---|
| API | `python -m uvicorn agents.dashboard_agent.api:create_app --factory --port 8100` (repo root) | 8100 |
| Frontend | `npm run build && npm run start -- -p 3100` (`frontend/`) | 3100 |

API env: `BIFLOW_DATASET_SET=sample`, `DASHBOARD_LAYOUT_PATH` and
`ANALYTICAL_TABLE_PATH` pointing into `.e2e-data/` (gitignored, wiped by a
`globalSetup` so every run starts with "no data yet"), `ALLOWED_ORIGINS=
http://localhost:3100`. Frontend env: `NEXT_PUBLIC_API_URL=http://localhost:8100`.
Ports 8100/3100 avoid clashing with the Docker stack on 8000/3000.

`workers: 1`, `fullyParallel: false`: all specs share one output directory.
Specs that need dashboard data call a helper that hits
`GET /api/pipeline/run?domain=e-commerce` and reads the stream to the end, so
they don't depend on spec order. The landing spec exercises the same run
through the UI.

## Tests (all `e-commerce`)

1. **Landing runs the real pipeline.** Pick the e-commerce profile, arm the
   run, see all five subsystems reach done, and land on `/dashboard`.
2. **Dashboard renders the sample run.** Findings appear before KPI tiles;
   the tile for revenue reads `R$68,048.73` (as the currency formatter
   renders it); `on_time_delivery_rate` reads `93.9%`; the tile with a
   warning finding (review score) is sorted ahead of tiles with none.
3. **Drill-down.** Selecting a KPI opens the panel and shows a table with
   rows, and its row count text matches `total_rows`.
4. **PDF export.** Clicking Download PDF produces a download whose bytes start
   with `%PDF`.
5. **Ask box.** With `/api/query` stubbed via `page.route` to return a fixed
   answer, submitting a question shows that answer.

Assertions use roles/visible text, not CSS classes, so restyling doesn't break
them. Where the existing markup has no stable hook, add an `aria-label` or
`data-testid` rather than matching on class names.

## CI

New `e2e` job in `.github/workflows/tests.yml`, alongside `pytest` and
`frontend`: checkout, set up Python 3.11 and Node 22, install Python deps as
the `pytest` job does, `npm ci`, `npx playwright install --with-deps
chromium`, `npm run e2e`. No Postgres needed (the API run does not pass a
database URL). On failure, upload the Playwright report as an artifact.

## Risks

- **Production build time.** `next build` inside `webServer` adds ~1 minute;
  the `webServer` timeout is raised to cover it.
- **Windows locally.** The API command uses `python`; on machines where that
  is not on `PATH` the config reads `PYTHON` from the environment.
- **Sample values drifting.** Exact figures come from the seeded sample and
  will only change if the sample data or KPI formulas change; that is a
  legitimate reason for these tests to fail.
- **Flake from the 5 s poll.** Assertions use Playwright's auto-waiting
  expectations, never fixed sleeps.

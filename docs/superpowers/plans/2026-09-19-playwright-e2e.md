# Playwright End-to-End Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a small Playwright suite that drives the real landing console and dashboard against a real API run on the committed sample data, and run it in CI.

**Architecture:** Playwright's `webServer` starts the FastAPI app (port 8100) and a production build of the Next.js frontend (port 3100). A new `BIFLOW_DATASET_SET=sample` env var makes `/api/pipeline/run` read `data/sample/*` instead of the gitignored `data/raw/*`. Output goes to a wiped-per-run `.e2e-data/` directory. Only Ollama's response is stubbed.

**Tech Stack:** `@playwright/test` (Chromium), FastAPI/uvicorn, Next.js 16, pytest, GitHub Actions.

**Spec:** [docs/superpowers/specs/2026-09-19-playwright-e2e-design.md](../specs/2026-09-19-playwright-e2e-design.md)

## Global Constraints

- All e2e tests use the `e-commerce` domain only.
- Ports: API `8100`, frontend `3100` (never `8000`/`3000`, which the Docker stack uses).
- `workers: 1`, `fullyParallel: false` (specs share one output directory).
- `reuseExistingServer: false` for both web servers.
- No fixed sleeps; use Playwright's auto-waiting `expect`.
- Assert on roles and visible text, never CSS class names.
- Chromium only.
- Production behaviour is unchanged when `BIFLOW_DATASET_SET` is unset.
- Commit messages end with `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>`.

---

## File Structure

| File | Responsibility |
|---|---|
| `agents/dashboard_agent/api.py` (modify) | `DATASET_SETS` mapping and `BIFLOW_DATASET_SET` resolution |
| `agents/dashboard_agent/tests/test_api.py` (modify) | pytest coverage of the resolver |
| `frontend/package.json` (modify) | `@playwright/test` dev dependency, `e2e` script |
| `frontend/jest.config.js` (modify) | keep Jest away from `e2e/` |
| `frontend/playwright.config.ts` (create) | servers, env, projects |
| `frontend/e2e/constants.ts` (create) | ports, URLs, data dir (shared by config and specs) |
| `frontend/e2e/global-setup.ts` (create) | wipe and recreate `.e2e-data/` |
| `frontend/e2e/helpers.ts` (create) | `runPipeline` helper |
| `frontend/e2e/landing.spec.ts` (create) | test 1 |
| `frontend/e2e/dashboard.spec.ts` (create) | tests 2 and 3 |
| `frontend/e2e/report-and-ask.spec.ts` (create) | tests 4 and 5 |
| `.gitignore`, `frontend/.gitignore` (modify) | ignore `.e2e-data/`, `playwright-report/`, `test-results/` |
| `.github/workflows/tests.yml` (modify) | `e2e` job |
| `frontend/README.md`, `docs/IMPLEMENTATION.md` (modify) | document it, drop the "no e2e" limitation |

---

### Task 1: `BIFLOW_DATASET_SET` in the API

**Files:**
- Modify: `agents/dashboard_agent/api.py:37-42` (the `DOMAIN_DATASETS` block) and `api.py:122` (its one use)
- Test: `agents/dashboard_agent/tests/test_api.py`

**Interfaces:**
- Produces: env var `BIFLOW_DATASET_SET` (`raw` default, or `sample`); module constant `DATASET_SETS: dict[str, dict[str, tuple[str, str]]]`. An unknown value makes `create_app()` raise `ValueError`.

- [ ] **Step 1: Make the fake orchestrator record the dataset it is given, and write the failing tests**

In `agents/dashboard_agent/tests/test_api.py`, change `_FakeOrchestrator`:

```python
class _FakeOrchestrator:
    """Stands in for BIFlowOrchestrator: emits events without touching real data."""

    STAGES = ["data_engineering", "kpi_semantic", "bi_analyst", "dashboard", "auditor"]
    last_analytical_path = None
    last_raw_dataset = None

    def __init__(self, analytical_path, dashboard_layout_path, on_event):
        _FakeOrchestrator.last_analytical_path = analytical_path
        self.on_event = on_event

    def run_pipeline(self, raw_dataset):
        _FakeOrchestrator.last_raw_dataset = raw_dataset
        for stage in self.STAGES:
            self.on_event(stage, "started", {})
            self.on_event(stage, "succeeded", {})
```

Append these tests to the end of the file:

```python
def test_run_pipeline_reads_the_raw_datasets_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("BIFLOW_DATASET_SET", raising=False)
    monkeypatch.setattr("agents.dashboard_agent.api.BIFlowOrchestrator", _FakeOrchestrator)
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    client.get("/api/pipeline/run", params={"domain": "banking"})

    assert _FakeOrchestrator.last_raw_dataset.dataset_path == "data/raw/berka"


def test_run_pipeline_reads_the_sample_datasets_when_configured(tmp_path, monkeypatch):
    monkeypatch.setenv("BIFLOW_DATASET_SET", "sample")
    monkeypatch.setattr("agents.dashboard_agent.api.BIFlowOrchestrator", _FakeOrchestrator)
    client = TestClient(create_app(layout_path=str(tmp_path / "dashboard_layout.json")))

    paths = {}
    for domain in ("e-commerce", "banking", "telco"):
        client.get("/api/pipeline/run", params={"domain": domain})
        paths[domain] = _FakeOrchestrator.last_raw_dataset.dataset_path

    assert paths == {
        "e-commerce": "data/sample/olist",
        "banking": "data/sample/banking",
        "telco": "data/sample/telco",
    }


def test_create_app_rejects_an_unknown_dataset_set(monkeypatch):
    monkeypatch.setenv("BIFLOW_DATASET_SET", "bogus")

    with pytest.raises(ValueError, match="BIFLOW_DATASET_SET"):
        create_app(layout_path="unused.json")
```

Add `import pytest` to the imports at the top of the file (after `import json`).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest agents/dashboard_agent/tests/test_api.py -q -k "dataset"`
Expected: the `sample` test FAILS (paths are still `data/raw/...`) and the `bogus` test FAILS (`DID NOT RAISE`). The `raw` default test passes.

- [ ] **Step 3: Implement**

In `agents/dashboard_agent/api.py`, replace the `DOMAIN_DATASETS` block:

```python
# Where each domain's dataset lives, for live-triggered runs. BIFLOW_DATASET_SET
# picks the set: "raw" (the full, gitignored datasets, the default) or "sample"
# (the small committed samples, used by the Playwright end-to-end tests).
# Directory names differ between the sets (berka vs banking), so these are two
# full mappings rather than one root.
DATASET_SETS: dict[str, dict[str, tuple[str, str]]] = {
    "raw": {
        "e-commerce": ("data/raw/olist", "olist"),
        "banking": ("data/raw/berka", "banking"),
        "telco": ("data/raw/telco", "telco"),
    },
    "sample": {
        "e-commerce": ("data/sample/olist", "olist"),
        "banking": ("data/sample/banking", "banking"),
        "telco": ("data/sample/telco", "telco"),
    },
}
```

In `create_app`, directly after `resolved_analytical_path = ...` add:

```python
    dataset_set = os.environ.get("BIFLOW_DATASET_SET", "raw")
    if dataset_set not in DATASET_SETS:
        raise ValueError(
            f"BIFLOW_DATASET_SET must be one of {sorted(DATASET_SETS)}, got {dataset_set!r}"
        )
    domain_datasets = DATASET_SETS[dataset_set]
```

Replace `dataset_path, dataset_name = DOMAIN_DATASETS[domain]` with `dataset_path, dataset_name = domain_datasets[domain]`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest agents/dashboard_agent -q`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add agents/dashboard_agent/api.py agents/dashboard_agent/tests/test_api.py
git commit -m "Let the API run the pipeline on sample data via BIFLOW_DATASET_SET"
```

---

### Task 2: Playwright scaffold and a first smoke test

**Files:**
- Modify: `frontend/package.json`, `frontend/jest.config.js`, `.gitignore`, `frontend/.gitignore`
- Create: `frontend/playwright.config.ts`, `frontend/e2e/constants.ts`, `frontend/e2e/global-setup.ts`, `frontend/e2e/helpers.ts`, `frontend/e2e/landing.spec.ts`

**Interfaces:**
- Produces (`e2e/constants.ts`): `API_PORT = 8100`, `WEB_PORT = 3100`, `API_URL`, `WEB_URL`, `REPO_ROOT`, `DATA_DIR`.
- Produces (`e2e/helpers.ts`): `runPipeline(request: APIRequestContext, domain?: string): Promise<void>`. Runs the real pipeline through `/api/pipeline/run` and throws if the stream does not contain `pipeline_succeeded`.
- Produces: `npm run e2e`.

- [ ] **Step 1: Install and wire up the scripts**

Run (in `frontend/`): `npm install --save-dev @playwright/test` then `npx playwright install chromium`.

In `frontend/package.json` add to `scripts`: `"e2e": "playwright test"`.

In `frontend/jest.config.js` add to `config`: `testPathIgnorePatterns: ["/node_modules/", "/.next/", "/e2e/"],`

Append to the root `.gitignore`:

```
# Playwright end-to-end run output
.e2e-data/
```

Append to `frontend/.gitignore`:

```
# playwright
/playwright-report/
/test-results/
```

- [ ] **Step 2: Write the shared files**

`frontend/e2e/constants.ts`:

```ts
import path from "node:path";

export const API_PORT = 8100;
export const WEB_PORT = 3100;
export const API_URL = `http://localhost:${API_PORT}`;
export const WEB_URL = `http://localhost:${WEB_PORT}`;
export const REPO_ROOT = path.resolve(__dirname, "..", "..");
export const DATA_DIR = path.join(REPO_ROOT, ".e2e-data");
```

`frontend/e2e/global-setup.ts`:

```ts
import fs from "node:fs";
import { DATA_DIR } from "./constants";

// Every run starts from "no dashboard data yet".
export default function globalSetup() {
  fs.rmSync(DATA_DIR, { recursive: true, force: true });
  fs.mkdirSync(DATA_DIR, { recursive: true });
}
```

`frontend/e2e/helpers.ts`:

```ts
import type { APIRequestContext } from "@playwright/test";
import { API_URL } from "./constants";

// Runs the real pipeline through the API (the same endpoint the landing page
// uses) and waits for the stream to end, so a spec can rely on dashboard data
// existing without depending on spec order.
export async function runPipeline(request: APIRequestContext, domain = "e-commerce") {
  const response = await request.get(`${API_URL}/api/pipeline/run`, {
    params: { domain },
    timeout: 120_000,
  });
  const body = await response.text();
  if (!body.includes('"pipeline_succeeded"')) {
    throw new Error(`Pipeline run for ${domain} did not succeed:\n${body}`);
  }
}
```

- [ ] **Step 3: Write the config**

`frontend/playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";
import path from "node:path";
import { API_PORT, API_URL, DATA_DIR, REPO_ROOT, WEB_PORT, WEB_URL } from "./e2e/constants";

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  // All specs share one output directory, so they run one at a time.
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: { baseURL: WEB_URL, trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `${process.env.PYTHON ?? "python"} -m uvicorn agents.dashboard_agent.api:create_app --factory --port ${API_PORT}`,
      cwd: REPO_ROOT,
      url: `${API_URL}/api/health`,
      reuseExistingServer: false,
      timeout: 60_000,
      env: {
        BIFLOW_DATASET_SET: "sample",
        DASHBOARD_LAYOUT_PATH: path.join(DATA_DIR, "dashboard_layout.json"),
        ANALYTICAL_TABLE_PATH: path.join(DATA_DIR, "analytical_table.csv"),
        ALLOWED_ORIGINS: WEB_URL,
      },
    },
    {
      // NEXT_PUBLIC_API_URL is baked in at build time, so it must be set here.
      command: `npm run build && npm run start -- -p ${WEB_PORT}`,
      cwd: __dirname,
      url: WEB_URL,
      reuseExistingServer: false,
      timeout: 240_000,
      env: { NEXT_PUBLIC_API_URL: API_URL },
    },
  ],
});
```

- [ ] **Step 4: Write the first (smoke) spec**

`frontend/e2e/landing.spec.ts`:

```ts
import { expect, test } from "@playwright/test";

test("the landing console loads with the run button disabled until a domain is chosen", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Run Pipeline" })).toBeDisabled();
  await expect(page.getByRole("button", { name: /Olist/ })).toBeVisible();
});
```

- [ ] **Step 5: Run it**

Run (in `frontend/`): `npm run e2e`
Expected: both servers start (the build takes about a minute), 1 test passes. Then run `npm test -- --ci` and confirm Jest does not pick up `e2e/` (still 60 tests, none from `e2e`).

- [ ] **Step 6: Commit**

```bash
git add .gitignore frontend/.gitignore frontend/package.json frontend/package-lock.json frontend/jest.config.js frontend/playwright.config.ts frontend/e2e
git commit -m "Scaffold Playwright with an API+frontend harness on sample data"
```

---

### Task 3: Landing runs the real pipeline

**Files:**
- Modify: `frontend/e2e/landing.spec.ts`

**Interfaces:**
- Consumes: the harness from Task 2.

The landing page redirects 500 ms after success, so this test asserts the redirect and the resulting dashboard rather than transient stage labels.

- [ ] **Step 1: Add the test**

Append to `frontend/e2e/landing.spec.ts`:

```ts
test("picking a domain and running the pipeline hands off to the dashboard", async ({ page }) => {
  await page.goto("/");

  const olist = page.getByRole("button", { name: /Olist/ });
  await olist.click();
  await expect(olist).toHaveAttribute("aria-pressed", "true");

  await page.getByRole("button", { name: "Run Pipeline" }).click();

  // A real run on the sample data; generous timeout for a cold start.
  await expect(page).toHaveURL(/\/dashboard\?domain=e-commerce/, { timeout: 90_000 });
  await expect(page.getByRole("heading", { name: /Findings/ })).toBeVisible();
  await expect(page.getByRole("heading", { name: /KPI telemetry/ })).toBeVisible();
});
```

- [ ] **Step 2: Run it**

Run: `npm run e2e -- landing.spec.ts`
Expected: 2 passed. If the `Findings` or `KPI telemetry` heading role query fails, run with `--headed` and read the real accessible names; fix the query, not the app.

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/landing.spec.ts
git commit -m "Test the landing console end to end"
```

---

### Task 4: Dashboard rendering and drill-down

**Files:**
- Create: `frontend/e2e/dashboard.spec.ts`

**Interfaces:**
- Consumes: `runPipeline`, `API_URL` from Tasks 2. Real sample values: revenue `68048.73`, on-time delivery `0.9385…`; the review-score KPI is the 4th KPI and carries a warning finding, so its tile is `KPI·04` and sorts first.

- [ ] **Step 1: Write the specs**

`frontend/e2e/dashboard.spec.ts`:

```ts
import { expect, test } from "@playwright/test";
import { API_URL } from "./constants";
import { runPipeline } from "./helpers";

test.beforeAll(async ({ request }) => {
  await runPipeline(request);
});

test("shows findings above the KPI wall, sorted by attention, with formatted values", async ({
  page,
}) => {
  await page.goto("/dashboard?domain=e-commerce");

  const findings = page.getByRole("heading", { name: /Findings/ });
  const wall = page.getByRole("heading", { name: /KPI telemetry/ });
  await expect(findings).toBeVisible();
  await expect(wall).toBeVisible();
  const findingsBox = await findings.boundingBox();
  const wallBox = await wall.boundingBox();
  expect(findingsBox!.y).toBeLessThan(wallBox!.y);

  const tiles = page.getByRole("region", { name: /KPI telemetry/ }).getByRole("button");
  await expect(tiles).toHaveCount(5);
  // The review-score KPI (KPI·04) carries a warning finding, so it sorts first.
  await expect(tiles.first()).toContainText("KPI·04");

  await expect(tiles.filter({ hasText: "R$68,048.73" })).toHaveCount(1);
  await expect(tiles.filter({ hasText: "93.9%" })).toHaveCount(1);
});

test("drilling into a KPI shows the rows behind its number", async ({ page, request }) => {
  const expected = await (
    await request.get(`${API_URL}/api/drilldown`, {
      params: { domain: "e-commerce", kpi: "total_revenue" },
    })
  ).json();

  await page.goto("/dashboard?domain=e-commerce");
  await page.getByRole("button", { name: /Total revenue/ }).first().click();

  const detail = page.getByTestId("kpi-detail");
  await expect(detail).toBeVisible();
  await detail.getByRole("button", { name: /View underlying rows/ }).click();

  await expect(detail.getByText(new RegExp(`${expected.total_rows} rows matched`))).toBeVisible();
  await expect(detail.locator("tbody tr")).toHaveCount(expected.rows.length);
  expect(expected.rows.length).toBeGreaterThan(0);
});
```

- [ ] **Step 2: Run them**

Run: `npm run e2e -- dashboard.spec.ts`
Expected: 2 passed. Known adjustments to verify on the first run, fixing the *test* only:
- If the revenue value renders as `R$ 68,048.73` (ICU/locale spacing), change the string to what the app actually renders.
- If `Total revenue` also matches an insight button, tighten with `.filter({ hasText: "R$" })` or use the tile's `aria-pressed` attribute.

- [ ] **Step 3: Commit**

```bash
git add frontend/e2e/dashboard.spec.ts
git commit -m "Test dashboard ordering, formatting and drill-down end to end"
```

---

### Task 5: PDF export and the Ask box

**Files:**
- Create: `frontend/e2e/report-and-ask.spec.ts`

**Interfaces:**
- Consumes: `runPipeline` from Task 2.

- [ ] **Step 1: Write the specs**

`frontend/e2e/report-and-ask.spec.ts`:

```ts
import { expect, test } from "@playwright/test";
import fs from "node:fs";
import { runPipeline } from "./helpers";

test.beforeAll(async ({ request }) => {
  await runPipeline(request);
});

test("the PDF link downloads a real PDF", async ({ page }) => {
  await page.goto("/dashboard?domain=e-commerce");

  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("link", { name: "Download PDF report" }).click(),
  ]);

  expect(download.suggestedFilename()).toBe("biflow_report.pdf");
  const bytes = fs.readFileSync(await download.path());
  expect(bytes.subarray(0, 4).toString()).toBe("%PDF");
});

test("the Ask box shows the answer from /api/query (Ollama stubbed)", async ({ page }) => {
  // Only the local LLM is stubbed; CI has no Ollama. The request is cross-origin,
  // so the stub sends CORS headers itself.
  await page.route("**/api/query*", (route) =>
    route.fulfill({
      status: 200,
      headers: { "access-control-allow-origin": "*", "access-control-allow-headers": "*" },
      json: { answer: "Stubbed answer: revenue was R$68,048.73." },
    })
  );

  await page.goto("/dashboard?domain=e-commerce");
  await page.getByPlaceholder("Ask a question about this dashboard…").fill("What was revenue?");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByText("Stubbed answer: revenue was R$68,048.73.")).toBeVisible();
  await expect(page.getByText("What was revenue?")).toBeVisible();
});
```

- [ ] **Step 2: Run them**

Run: `npm run e2e -- report-and-ask.spec.ts`
Expected: 2 passed. If the stubbed POST fails on the CORS preflight, add `"access-control-allow-methods": "POST, OPTIONS"` to the stub's headers.

- [ ] **Step 3: Run the whole suite twice**

Run: `npm run e2e` twice in a row.
Expected: 6 passed both times (proves the wiped-directory start and shared-directory ordering are stable).

- [ ] **Step 4: Commit**

```bash
git add frontend/e2e/report-and-ask.spec.ts
git commit -m "Test PDF download and the Ask box end to end"
```

---

### Task 6: CI job and docs

**Files:**
- Modify: `.github/workflows/tests.yml`, `frontend/README.md`, `docs/IMPLEMENTATION.md`

- [ ] **Step 1: Add the CI job**

Append to `jobs:` in `.github/workflows/tests.yml`:

```yaml
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install Python dependencies
        run: |
          pip install -r requirements-dev.txt
          for req in agents/*/requirements.txt orchestrator/requirements.txt; do
            pip install -r "$req"
          done

      - uses: actions/setup-node@v4
        with:
          node-version: "22"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install frontend dependencies
        working-directory: frontend
        run: npm ci

      - name: Install Chromium
        working-directory: frontend
        run: npx playwright install --with-deps chromium

      - name: Run end-to-end tests
        working-directory: frontend
        run: npm run e2e

      - name: Upload Playwright report
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

- [ ] **Step 2: Update the docs**

In `frontend/README.md`, under `## Testing`, add after the code block:

```markdown
### End-to-end (Playwright)

```bash
npx playwright install chromium   # once
npm run e2e
```

Starts the API (port 8100) and a production build of the frontend (port 3100)
itself, against the committed **sample** data (`BIFLOW_DATASET_SET=sample`), and
drives the real landing console and dashboard. Only Ollama's answer is stubbed.
Output goes to `.e2e-data/` at the repo root (gitignored, wiped each run). Set
`PYTHON` if `python` is not on your `PATH`.
```

Change the README TODO line `- [ ] End-to-end tests (Playwright) ...` to `- [x] End-to-end tests (Playwright) — see \`e2e/\``.

In `docs/IMPLEMENTATION.md` section 13, replace the bullet beginning `- **No end-to-end (Playwright) frontend tests**` (through its end) with:

```markdown
- **End-to-end tests cover one domain** — the Playwright suite (`frontend/e2e/`) runs the golden path for `e-commerce` on the sample data; banking and telco are covered by pytest and Jest only.
```

- [ ] **Step 3: Verify**

Run: `python -m pytest -q` and, in `frontend/`, `npm test -- --ci`, `npm run lint`, `npm run build`, `npm run e2e`.
Expected: all green (lint's one pre-existing `page.tsx` warning is acceptable).

- [ ] **Step 4: Commit, push, open the PR**

```bash
git add .github/workflows/tests.yml frontend/README.md docs/IMPLEMENTATION.md
git commit -m "Run Playwright in CI and document the e2e suite"
git push -u origin playwright-e2e
gh pr create --base main --head playwright-e2e --title "Add Playwright end-to-end tests"
```

Then watch the `e2e` job on the PR. The first CI run is the real test of the workflow; fix what it shows.

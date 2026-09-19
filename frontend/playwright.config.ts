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
  projects: [
    {
      name: "chromium",
      // Set E2E_BROWSER_CHANNEL=chrome to drive an installed Chrome instead of
      // downloading Playwright's Chromium (handy on slow or restricted networks).
      // Unset (the default, and what CI uses) means the bundled Chromium.
      use: { ...devices["Desktop Chrome"], channel: process.env.E2E_BROWSER_CHANNEL || undefined },
    },
  ],
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

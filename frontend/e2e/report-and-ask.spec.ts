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

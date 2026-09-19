import { expect, test } from "@playwright/test";

test("the landing console loads with the run button disabled until a domain is chosen", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Run Pipeline" })).toBeDisabled();
  await expect(page.getByRole("button", { name: /Olist/ })).toBeVisible();
});

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

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
  // Sorted by attention, ties keeping the original order: warnings (revenue
  // KPI·01, review score KPI·04), then info (order count KPI·03, on-time
  // delivery KPI·05), then the KPI with no findings (average order value KPI·02).
  await expect(tiles).toHaveText([/^KPI·01/, /^KPI·04/, /^KPI·03/, /^KPI·05/, /^KPI·02/]);

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

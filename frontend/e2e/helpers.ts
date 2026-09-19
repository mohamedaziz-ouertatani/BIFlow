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

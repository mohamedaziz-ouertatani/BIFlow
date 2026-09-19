import { metricAxisDomain, truncateAxisLabel } from "./axes";

describe("metricAxisDomain", () => {
  it("pins bar charts of the 1-5 review score to 0-5 instead of an auto range up to 8", () => {
    expect(metricAxisDomain("average_review_score", "bar")).toEqual([0, 5]);
  });

  it("lets a review score trend line zoom into the 1-5 rating scale", () => {
    expect(metricAxisDomain("average_review_score", "line")).toEqual([1, 5]);
  });

  it("leaves every other metric on the automatic range from zero", () => {
    expect(metricAxisDomain("total_revenue", "bar")).toEqual([0, "auto"]);
    expect(metricAxisDomain("churn_rate", "line")).toEqual([0, "auto"]);
  });
});

describe("truncateAxisLabel", () => {
  it("keeps short labels unchanged", () => {
    expect(truncateAxisLabel("health_beauty")).toBe("health_beauty");
  });

  it("cuts long labels from the end with an ellipsis so the start stays readable", () => {
    const result = truncateAxisLabel("computers_accessories");
    expect(result).toBe("computers_acc…");
    expect(result).toHaveLength(14);
  });
});

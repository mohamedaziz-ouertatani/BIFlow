import { formatMetricValue, formatMetricValueCompact } from "./currency";

describe("formatMetricValue", () => {
  it("formats rate KPIs as percentages with at most one decimal", () => {
    expect(formatMetricValue("churn_rate", 0.2653698)).toBe("26.5%");
    expect(formatMetricValue("on_time_delivery_rate", 0.9)).toBe("90%");
    expect(formatMetricValue("loan_good_standing_rate", 0.881183)).toBe("88.1%");
  });

  it("keeps currency formatting for monetary KPIs", () => {
    expect(formatMetricValue("average_monthly_charges", 64.76)).toBe("$64.76");
  });

  it("leaves other metrics as plain numbers", () => {
    expect(formatMetricValue("total_customers", 7043)).toBe("7043");
    expect(formatMetricValue("average_review_score", 4.123)).toBe("4.12");
  });
});

describe("formatMetricValueCompact", () => {
  it("formats rate KPIs as percentages", () => {
    expect(formatMetricValueCompact("churn_rate", 0.4271)).toBe("42.7%");
  });

  it("still compacts large plain numbers", () => {
    expect(formatMetricValueCompact("total_customers", 12500)).toBe("12.5K");
  });
});

import { render, screen } from "@testing-library/react";
import TrendChart from "./TrendChart";

describe("TrendChart", () => {
  it("renders the human-readable label for a known metric", () => {
    render(
      <TrendChart
        metric="total_revenue"
        series={[
          { month: "2018-01", value: 100 },
          { month: "2018-02", value: 150 },
        ]}
      />
    );

    expect(screen.getByText("Revenue")).toBeInTheDocument();
  });

  it("falls back to the raw metric name when there's no known label", () => {
    render(
      <TrendChart
        metric="some_new_metric"
        series={[
          { month: "2018-01", value: 1 },
          { month: "2018-02", value: 2 },
        ]}
      />
    );

    expect(screen.getByText("some_new_metric")).toBeInTheDocument();
  });
});

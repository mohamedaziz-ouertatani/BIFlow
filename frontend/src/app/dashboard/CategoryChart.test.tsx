import { render, screen } from "@testing-library/react";
import CategoryChart from "./CategoryChart";

describe("CategoryChart", () => {
  it("renders the human-readable metric label and dimension for a known key", () => {
    render(
      <CategoryChart
        breakdownKey="total_revenue_by_category"
        points={[
          { label: "electronics", value: 200 },
          { label: "books", value: 100 },
        ]}
      />
    );

    expect(screen.getByText("Revenue by category")).toBeInTheDocument();
  });

  it("falls back to the raw metric name when there's no known label", () => {
    render(
      <CategoryChart
        breakdownKey="some_new_metric_by_region"
        points={[{ label: "north", value: 1 }]}
      />
    );

    expect(screen.getByText("some_new_metric by region")).toBeInTheDocument();
  });

  it("labels telco metrics and dimensions readably", () => {
    render(
      <CategoryChart
        breakdownKey="churn_rate_by_internet_service"
        points={[{ label: "Fiber optic", value: 0.417 }]}
      />
    );

    expect(screen.getByText("Churn rate by internet service")).toBeInTheDocument();
  });

  it("labels the banking loan metric by region", () => {
    render(
      <CategoryChart
        breakdownKey="loan_good_standing_rate_by_region"
        points={[{ label: "Prague", value: 0.9 }]}
      />
    );

    expect(screen.getByText("Loan good standing rate by region")).toBeInTheDocument();
  });
});

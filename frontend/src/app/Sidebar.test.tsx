import { fireEvent, render, screen } from "@testing-library/react";
import Sidebar from "./Sidebar";

describe("Sidebar", () => {
  it("renders the brand, domain badge, and section nav links", () => {
    render(
      <Sidebar
        domain="banking"
        lastUpdated={null}
        reportUrl={null}
        askOpen={true}
        onToggleAsk={() => {}}
      />
    );

    expect(screen.getByText("BIFlow")).toBeInTheDocument();
    expect(screen.getByText("banking")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Overview" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Trends" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Insights" })).toBeInTheDocument();
  });

  it("only renders the PDF report link when a report URL is provided", () => {
    const { rerender } = render(
      <Sidebar
        domain={null}
        lastUpdated={null}
        reportUrl={null}
        askOpen={true}
        onToggleAsk={() => {}}
      />
    );
    expect(screen.queryByText("Download PDF report")).not.toBeInTheDocument();

    rerender(
      <Sidebar
        domain={null}
        lastUpdated={null}
        reportUrl="http://localhost:8000/api/report.pdf"
        askOpen={true}
        onToggleAsk={() => {}}
      />
    );
    const link = screen.getByText("Download PDF report") as HTMLAnchorElement;
    expect(link.closest("a")).toHaveAttribute("href", "http://localhost:8000/api/report.pdf");
  });

  it("calls onToggleAsk and reflects the open/closed label when the ask toggle is clicked", () => {
    const onToggleAsk = jest.fn();
    render(
      <Sidebar
        domain={null}
        lastUpdated={null}
        reportUrl={null}
        askOpen={true}
        onToggleAsk={onToggleAsk}
      />
    );

    const toggle = screen.getByRole("button", { name: "Hide ask panel" });
    fireEvent.click(toggle);
    expect(onToggleAsk).toHaveBeenCalledTimes(1);
  });
});

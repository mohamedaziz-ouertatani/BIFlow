import { fireEvent, render, screen } from "@testing-library/react";
import Sidebar from "./Sidebar";

describe("Sidebar", () => {
  it("renders the brand and domain badge", () => {
    render(
      <Sidebar
        domain="banking"
        lastUpdated={null}
        reportUrl={null}
        askOpen={true}
        onToggleAsk={() => {}}
        onRefresh={() => {}}
      />
    );

    expect(screen.getByText("BIFlow")).toBeInTheDocument();
    expect(screen.getByText("banking")).toBeInTheDocument();
  });

  it("only renders the PDF report link when a report URL is provided", () => {
    const { rerender } = render(
      <Sidebar
        domain={null}
        lastUpdated={null}
        reportUrl={null}
        askOpen={true}
        onToggleAsk={() => {}}
        onRefresh={() => {}}
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
        onRefresh={() => {}}
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
        onRefresh={() => {}}
      />
    );

    const toggle = screen.getByRole("button", { name: "Hide ask panel" });
    fireEvent.click(toggle);
    expect(onToggleAsk).toHaveBeenCalledTimes(1);
  });

  it("calls onRefresh when the refresh button is clicked", () => {
    const onRefresh = jest.fn();
    render(
      <Sidebar
        domain={null}
        lastUpdated={null}
        reportUrl={null}
        askOpen={true}
        onToggleAsk={() => {}}
        onRefresh={onRefresh}
      />
    );

    fireEvent.click(screen.getByRole("button", { name: "Refresh now" }));
    expect(onRefresh).toHaveBeenCalledTimes(1);
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import DrillDownPanel from "./DrillDownPanel";

function mockFetchOnce(response: Partial<Response> & { jsonBody?: unknown }) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: response.ok ?? true,
    status: response.status ?? 200,
    json: async () => response.jsonBody,
  } as Response);
}

afterEach(() => {
  jest.restoreAllMocks();
});

describe("DrillDownPanel", () => {
  it("starts collapsed and does not fetch until toggled", () => {
    global.fetch = jest.fn();
    render(<DrillDownPanel domain="e-commerce" kpiName="total_revenue" />);

    expect(screen.getByText(/view underlying rows/i)).toBeInTheDocument();
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it("fetches and renders rows when toggled open", async () => {
    mockFetchOnce({
      jsonBody: {
        total_rows: 1,
        columns: ["order_id", "price"],
        rows: [{ order_id: "o1", price: 100 }],
      },
    });

    render(<DrillDownPanel domain="e-commerce" kpiName="total_revenue" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));

    expect(await screen.findByText("o1")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText(/1 row matched/i)).toBeInTheDocument();

    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("domain=e-commerce");
    expect(url).toContain("kpi=total_revenue");
  });

  it("includes the month in the request when given", async () => {
    mockFetchOnce({ jsonBody: { total_rows: 0, columns: [], rows: [] } });

    render(
      <DrillDownPanel domain="banking" kpiName="total_transaction_volume" month="2018-02" />
    );
    fireEvent.click(screen.getByText(/view underlying rows/i));

    await waitFor(() => expect(global.fetch).toHaveBeenCalled());
    const [url] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toContain("month=2018-02");
  });

  it("does not start the summary with a separator when there is no formula", async () => {
    mockFetchOnce({
      jsonBody: { total_rows: 2, columns: ["order_id"], rows: [{ order_id: "o1" }, { order_id: "o2" }] },
    });

    render(<DrillDownPanel domain="e-commerce" kpiName="total_revenue" month="2018-08" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));

    const summary = await screen.findByText(/2 rows matched/i);
    expect(summary.textContent?.trim()).toBe("2018-08 · 2 rows matched");
  });

  it("shows a note when the row cap is hit", async () => {
    mockFetchOnce({
      jsonBody: {
        total_rows: 60,
        columns: ["order_id"],
        rows: Array.from({ length: 50 }, (_, i) => ({ order_id: `o${i}` })),
      },
    });

    render(<DrillDownPanel domain="e-commerce" kpiName="order_count" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));

    expect(await screen.findByText(/showing first 50/i)).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    mockFetchOnce({ ok: false, status: 404, jsonBody: { detail: "Unknown KPI: 'x'" } });

    render(<DrillDownPanel domain="e-commerce" kpiName="x" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));

    expect(await screen.findByText("Unknown KPI: 'x'")).toBeInTheDocument();
  });

  it("collapses again when toggled a second time", async () => {
    mockFetchOnce({
      jsonBody: { total_rows: 1, columns: ["order_id"], rows: [{ order_id: "o1" }] },
    });

    render(<DrillDownPanel domain="e-commerce" kpiName="total_revenue" />);
    fireEvent.click(screen.getByText(/view underlying rows/i));
    await screen.findByText("o1");

    fireEvent.click(screen.getByText(/hide underlying rows/i));
    expect(screen.queryByText("o1")).not.toBeInTheDocument();
  });
});

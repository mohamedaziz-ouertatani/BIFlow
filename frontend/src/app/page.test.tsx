import { render, screen, waitFor } from "@testing-library/react";
import DashboardPage from "./page";
import type { DashboardLayout } from "./types";

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

describe("DashboardPage", () => {
  it("renders KPI cards, trend charts, and insights from the API response", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [
        { name: "total_revenue", label: "Total revenue", value: 123.45 },
      ],
      insights: [
        { title: "Revenue up", description: "Grew 10%", severity: "info" },
      ],
      monthly_trends: {
        total_revenue: [
          { month: "2018-01", value: 100 },
          { month: "2018-02", value: 150 },
        ],
      },
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);

    expect(await screen.findByText("123.45")).toBeInTheDocument();
    expect(screen.getByText("Revenue up", { exact: false })).toBeInTheDocument();
    expect(screen.getByText("Revenue")).toBeInTheDocument(); // trend chart label
  });

  it("shows a no-data message when the API returns 404", async () => {
    mockFetchOnce({ ok: false, status: 404, jsonBody: {} });

    render(<DashboardPage />);

    expect(
      await screen.findByText(/no dashboard data yet/i)
    ).toBeInTheDocument();
  });

  it("shows an error message when the API is unreachable", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("network down"));

    render(<DashboardPage />);

    expect(
      await screen.findByText(/could not reach the dashboard api/i)
    ).toBeInTheDocument();
  });

  it("polls the API again after the interval elapses", async () => {
    jest.useFakeTimers({ advanceTimers: true });
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    jest.advanceTimersByTime(5000);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));

    jest.useRealTimers();
  });
});

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import DashboardPage from "./page";
import type { DashboardLayout } from "./types";

const mockSearchParams = { get: jest.fn() };
jest.mock("next/navigation", () => ({
  useSearchParams: () => mockSearchParams,
}));

function mockFetchOnce(response: Partial<Response> & { jsonBody?: unknown }) {
  global.fetch = jest.fn().mockResolvedValue({
    ok: response.ok ?? true,
    status: response.status ?? 200,
    json: async () => response.jsonBody,
  } as Response);
}

function goToTab(name: string) {
  fireEvent.click(screen.getByRole("tab", { name: new RegExp(`^${name}`) }));
}

beforeEach(() => {
  mockSearchParams.get.mockReturnValue(null);
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("DashboardPage", () => {
  it("renders KPI cards on the Overview tab by default", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [
        { name: "total_revenue", label: "Total revenue", value: 123.45 },
      ],
      insights: [
        {
          title: "Revenue up",
          description: "Grew 10%",
          related_kpi: "total_revenue",
          severity: "info",
        },
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

    expect(await screen.findByText("R$123.45")).toBeInTheDocument();
    expect(screen.queryByText("Revenue up", { exact: false })).not.toBeInTheDocument();
  });

  it("shows trend charts on the Trends tab", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [{ name: "total_revenue", label: "Total revenue", value: 123.45 }],
      insights: [],
      monthly_trends: {
        total_revenue: [
          { month: "2018-01", value: 100 },
          { month: "2018-02", value: 150 },
        ],
      },
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByText("R$123.45");
    goToTab("Trends");

    expect(screen.getByText("Revenue")).toBeInTheDocument(); // trend chart label
  });

  it("shows insights on their own tab", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [{ name: "total_revenue", label: "Total revenue", value: 123.45 }],
      insights: [
        {
          title: "Revenue up",
          description: "Grew 10%",
          related_kpi: "total_revenue",
          severity: "info",
        },
      ],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByText("R$123.45");
    goToTab("Insights");

    expect(screen.getByText("Revenue up", { exact: false })).toBeInTheDocument();
  });

  it("shows a KPI's explanation and related insights when its card is clicked", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [
        {
          name: "total_revenue",
          label: "Total revenue",
          value: 123.45,
          explanation: "total_revenue = sum(price) = 123.45",
        },
      ],
      insights: [
        {
          title: "Revenue up",
          description: "Grew 10%",
          related_kpi: "total_revenue",
          severity: "info",
        },
        {
          title: "Unrelated insight",
          description: "About something else",
          related_kpi: "order_count",
          severity: "info",
        },
      ],
      monthly_trends: {
        total_revenue: [{ month: "2018-01", value: 100 }],
      },
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    fireEvent.click(await screen.findByText("Total revenue"));

    const detail = within(await screen.findByTestId("kpi-detail"));
    expect(detail.getByText("total_revenue = sum(price) = 123.45")).toBeInTheDocument();
    expect(detail.getByText("Revenue up", { exact: false })).toBeInTheDocument();
    expect(detail.queryByText("Unrelated insight", { exact: false })).not.toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Close KPI details"));
    expect(screen.queryByTestId("kpi-detail")).not.toBeInTheDocument();
  });

  it("shows a month-over-month comparison badge when the KPI has one", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [
        {
          name: "total_revenue",
          label: "Total revenue",
          value: 150,
          comparison: {
            previous_month: "2018-01",
            latest_month: "2018-02",
            previous_value: 100,
            latest_value: 150,
            pct_change: 50,
            direction: "increasing",
          },
        },
        { name: "order_count", label: "Order count", value: 10, comparison: null },
      ],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);

    expect(await screen.findByText("▲ 50.0% vs 2018-01")).toBeInTheDocument();
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

  it("fetches and links to the report scoped to the domain in the URL", async () => {
    mockSearchParams.get.mockReturnValue("banking");
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);

    await waitFor(() =>
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/dashboard?domain=banking",
        expect.anything()
      )
    );
    const link = (await screen.findByText("Download PDF report")) as HTMLAnchorElement;
    expect(link.closest("a")).toHaveAttribute(
      "href",
      "http://localhost:8000/api/report.pdf?domain=banking"
    );
  });

  it("renders a PDF report download link once the dashboard has loaded", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);

    const link = (await screen.findByText("Download PDF report")) as HTMLAnchorElement;
    expect(link.closest("a")).toHaveAttribute("href", "http://localhost:8000/api/report.pdf");
  });

  it("renders the query box once the dashboard has loaded", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);

    expect(await screen.findByText("Ask the dashboard")).toBeInTheDocument();
  });

  it("renders a category breakdown chart on the Breakdowns tab when the API returns one", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [],
      monthly_trends: {},
      category_breakdowns: {
        total_revenue_by_category: [
          { label: "electronics", value: 200 },
          { label: "books", value: 100 },
        ],
      },
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByText("Ask the dashboard");
    goToTab("Breakdowns");

    expect(await screen.findByText("Revenue by category")).toBeInTheDocument();
  });

  it("hides the ask panel when the sidebar toggle is clicked", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByText("Ask the dashboard");

    fireEvent.click(screen.getByRole("button", { name: "Hide ask panel" }));

    expect(screen.getByRole("button", { name: "Ask the dashboard" })).toBeInTheDocument();
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

  it("moves between tabs with arrow keys and updates aria-selected", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [{ title: "Revenue up", description: "Grew 10%", related_kpi: "x", severity: "info" }],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByText("Ask the dashboard");

    const overviewTab = screen.getByRole("tab", { name: /^Overview/ });
    expect(overviewTab).toHaveAttribute("aria-selected", "true");

    fireEvent.keyDown(overviewTab, { key: "ArrowRight" });
    const trendsTab = screen.getByRole("tab", { name: /^Trends/ });
    expect(trendsTab).toHaveAttribute("aria-selected", "true");
    expect(overviewTab).toHaveAttribute("aria-selected", "false");
  });

  it("refreshes immediately when the sidebar refresh button is clicked", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole("button", { name: "Refresh now" }));
    await waitFor(() => expect(global.fetch).toHaveBeenCalledTimes(2));
  });
});

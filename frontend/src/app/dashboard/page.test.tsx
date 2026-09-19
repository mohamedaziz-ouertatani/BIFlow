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

beforeEach(() => {
  mockSearchParams.get.mockReturnValue(null);
});

afterEach(() => {
  jest.restoreAllMocks();
});

describe("DashboardPage", () => {
  it("shows rate KPIs as percentages on their tiles", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [{ name: "churn_rate", label: "Share of customers who have churned.", value: 0.26537 }],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);

    expect(await screen.findByText("26.5%")).toBeInTheDocument();
  });

  it("renders KPI tiles and the findings log together, without tabs", async () => {
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
    expect(screen.getByText("Revenue up", { exact: false })).toBeInTheDocument();
    expect(screen.queryByRole("tab")).not.toBeInTheDocument();
  });

  it("sorts KPI tiles by attention, critical first, and shows each tile's formula", async () => {
    const layout: DashboardLayout = {
      kpi_cards: [
        { name: "order_count", label: "Order count", value: 10, explanation: "order_count = 10" },
        { name: "total_revenue", label: "Total revenue", value: 5, explanation: "total_revenue = 5" },
        { name: "average_review_score", label: "Review score", value: 4 },
      ],
      insights: [
        { title: "Revenue crashed", description: "Down", related_kpi: "total_revenue", severity: "critical" },
        { title: "Score note", description: "Fine", related_kpi: "average_review_score", severity: "warning" },
      ],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByText("Order count");

    const tiles = screen.getAllByRole("button", { pressed: false }).filter((b) =>
      b.className.includes("tile")
    );
    expect(tiles.map((t) => within(t).getByText(/Total revenue|Review score|Order count/).textContent)).toEqual([
      "Total revenue",
      "Review score",
      "Order count",
    ]);
    expect(screen.getByText("total_revenue = 5")).toBeInTheDocument();
    expect(screen.getByText("No findings")).toBeInTheDocument();
  });

  it("shows trend charts on the same page", async () => {
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

    expect(screen.getByText("Revenue")).toBeInTheDocument(); // trend chart label
  });

  it("lists insights in the findings log", async () => {
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

    expect(screen.getByRole("heading", { name: "Findings" })).toBeInTheDocument();
    expect(screen.getByText("Revenue up", { exact: false })).toBeInTheDocument();
  });

  it("expands a drill-down panel when an insight is clicked", async () => {
    mockSearchParams.get.mockReturnValue("e-commerce");
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [
        {
          title: "Revenue up",
          description: "Grew 10%",
          related_kpi: "total_revenue",
          severity: "info",
          month: "2018-02",
        },
      ],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByRole("heading", { name: "Findings" });
    fireEvent.click(screen.getByText("Revenue up", { exact: false }));

    expect(await screen.findByText(/view underlying rows/i)).toBeInTheDocument();
  });

  it("does not make an insight with no related KPI clickable", async () => {
    mockSearchParams.get.mockReturnValue("telco");
    const layout: DashboardLayout = {
      kpi_cards: [],
      insights: [
        {
          title: "No month-over-month trends available",
          description: "The telco dataset has no transaction dates.",
          related_kpi: "",
          severity: "info",
        },
      ],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    await screen.findByRole("heading", { name: "Findings" });

    expect(
      screen.queryByRole("button", { name: /no month-over-month trends available/i })
    ).not.toBeInTheDocument();
    expect(
      screen.getByText("No month-over-month trends available", { exact: false })
    ).toBeInTheDocument();
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

  it("shows a drill-down toggle in the KPI detail panel when a domain is set", async () => {
    mockSearchParams.get.mockReturnValue("e-commerce");
    const layout: DashboardLayout = {
      kpi_cards: [
        {
          name: "total_revenue",
          label: "Total revenue",
          value: 123.45,
          explanation: "total_revenue = sum(price) = 123.45",
        },
      ],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    fireEvent.click(await screen.findByText("Total revenue"));

    const detail = within(await screen.findByTestId("kpi-detail"));
    expect(detail.getByText(/view underlying rows/i)).toBeInTheDocument();
  });

  it("does not show a drill-down toggle when no domain is set", async () => {
    mockSearchParams.get.mockReturnValue(null);
    const layout: DashboardLayout = {
      kpi_cards: [{ name: "total_revenue", label: "Total revenue", value: 123.45 }],
      insights: [],
      monthly_trends: {},
    };
    mockFetchOnce({ jsonBody: layout });

    render(<DashboardPage />);
    fireEvent.click(await screen.findByText("Total revenue"));

    const detail = within(await screen.findByTestId("kpi-detail"));
    expect(detail.queryByText(/view underlying rows/i)).not.toBeInTheDocument();
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

  it("renders a category breakdown chart when the API returns one", async () => {
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

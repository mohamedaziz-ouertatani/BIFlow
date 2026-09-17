import { act, fireEvent, render, screen } from "@testing-library/react";
import LandingPage from "./page";

const push = jest.fn();
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

class MockEventSource {
  static instances: MockEventSource[] = [];
  url: string;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  emit(data: unknown) {
    this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent);
  }

  close() {
    this.closed = true;
  }
}

function latestSource() {
  return MockEventSource.instances[MockEventSource.instances.length - 1];
}

beforeEach(() => {
  MockEventSource.instances = [];
  push.mockClear();
  (global as unknown as { EventSource: unknown }).EventSource = MockEventSource;
});

describe("LandingPage", () => {
  it("disables Run Pipeline until a domain is selected", () => {
    render(<LandingPage />);

    expect(screen.getByRole("button", { name: "Run Pipeline" })).toBeDisabled();
    expect(screen.getByText("Choose a domain to enable the run.")).toBeInTheDocument();
  });

  it("announces the active stage as real events arrive", () => {
    render(<LandingPage />);
    fireEvent.click(screen.getByRole("button", { name: /Berka/ }));
    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    act(() => latestSource().emit({ type: "stage_started", stage: "kpi_semantic" }));

    expect(screen.getByText("KPI & Semantic: Computing KPIs...")).toBeInTheDocument();
  });

  it("shows an error and offers a retry when a stage fails", () => {
    render(<LandingPage />);
    fireEvent.click(screen.getByRole("button", { name: /Berka/ }));
    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    act(() => latestSource().emit({ type: "stage_started", stage: "kpi_semantic" }));
    act(() =>
      latestSource().emit({ type: "stage_failed", stage: "kpi_semantic", error: "boom" })
    );
    act(() =>
      latestSource().emit({ type: "pipeline_failed", stage: "kpi_semantic", error: "boom" })
    );

    expect(screen.getByText("boom", { selector: "p" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry Pipeline" })).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("navigates to the dashboard once the pipeline succeeds", () => {
    jest.useFakeTimers();
    render(<LandingPage />);
    fireEvent.click(screen.getByRole("button", { name: /Berka/ }));
    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));

    act(() => latestSource().emit({ type: "pipeline_succeeded" }));
    act(() => jest.advanceTimersByTime(500));

    expect(push).toHaveBeenCalledWith("/dashboard?domain=banking");
    jest.useRealTimers();
  });

  it("resets the graph when switching domains after a run finishes", () => {
    render(<LandingPage />);
    fireEvent.click(screen.getByRole("button", { name: /Berka/ }));
    fireEvent.click(screen.getByRole("button", { name: "Run Pipeline" }));
    act(() =>
      latestSource().emit({ type: "pipeline_failed", stage: "kpi_semantic", error: "boom" })
    );
    expect(screen.getByText("boom", { selector: "p" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Telco/ }));

    expect(screen.queryByText("boom", { selector: "p" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Run Pipeline" })).toBeInTheDocument();
  });
});

import { act, renderHook } from "@testing-library/react";
import { usePipelineRun } from "./usePipelineRun";

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

  triggerError() {
    this.onerror?.();
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
  (global as unknown as { EventSource: unknown }).EventSource = MockEventSource;
});

describe("usePipelineRun", () => {
  it("starts idle with every stage idle", () => {
    const { result } = renderHook(() => usePipelineRun());

    expect(result.current.state.status).toBe("idle");
    expect(result.current.state.stages.orchestrator).toBe("idle");
    expect(result.current.state.stages.data_engineering).toBe("idle");
  });

  it("marks the orchestrator active and connects scoped to the chosen domain", () => {
    const { result } = renderHook(() => usePipelineRun());

    act(() => result.current.run("banking"));

    expect(result.current.state.status).toBe("running");
    expect(result.current.state.stages.orchestrator).toBe("active");
    expect(latestSource().url).toContain("/api/pipeline/run?domain=banking");
  });

  it("moves a stage through active then done as real events arrive", () => {
    const { result } = renderHook(() => usePipelineRun());
    act(() => result.current.run("banking"));

    act(() => latestSource().emit({ type: "stage_started", stage: "data_engineering" }));
    expect(result.current.state.stages.data_engineering).toBe("active");
    expect(result.current.state.stages.orchestrator).toBe("done");

    act(() => latestSource().emit({ type: "stage_succeeded", stage: "data_engineering" }));
    expect(result.current.state.stages.data_engineering).toBe("done");
  });

  it("marks the stage errored and the run failed on stage_failed + pipeline_failed", () => {
    const { result } = renderHook(() => usePipelineRun());
    act(() => result.current.run("banking"));

    act(() => latestSource().emit({ type: "stage_started", stage: "kpi_semantic" }));
    act(() => latestSource().emit({ type: "stage_failed", stage: "kpi_semantic", error: "boom" }));
    act(() =>
      latestSource().emit({ type: "pipeline_failed", stage: "kpi_semantic", error: "boom" })
    );

    expect(result.current.state.stages.kpi_semantic).toBe("error");
    expect(result.current.state.status).toBe("failed");
    expect(result.current.state.error).toBe("boom");
    expect(latestSource().closed).toBe(true);
  });

  it("marks the run succeeded and closes the connection on pipeline_succeeded", () => {
    const { result } = renderHook(() => usePipelineRun());
    act(() => result.current.run("banking"));

    act(() => latestSource().emit({ type: "pipeline_succeeded" }));

    expect(result.current.state.status).toBe("succeeded");
    expect(latestSource().closed).toBe(true);
  });

  it("fails the run with a connection message if the stream errors mid-run", () => {
    const { result } = renderHook(() => usePipelineRun());
    act(() => result.current.run("banking"));

    act(() => latestSource().triggerError());

    expect(result.current.state.status).toBe("failed");
    expect(result.current.state.error).toBe("Lost connection to the pipeline.");
    expect(latestSource().closed).toBe(true);
  });

  it("ignores a stream error once the pipeline already finished", () => {
    const { result } = renderHook(() => usePipelineRun());
    act(() => result.current.run("banking"));
    act(() => latestSource().emit({ type: "pipeline_succeeded" }));

    act(() => latestSource().triggerError());

    expect(result.current.state.status).toBe("succeeded");
  });

  it("reset returns to the idle state", () => {
    const { result } = renderHook(() => usePipelineRun());
    act(() => result.current.run("banking"));
    act(() => latestSource().emit({ type: "pipeline_succeeded" }));

    act(() => result.current.reset());

    expect(result.current.state.status).toBe("idle");
    expect(result.current.state.stages.orchestrator).toBe("idle");
  });
});

import { render } from "@testing-library/react";
import PipelineGraph from "./PipelineGraph";
import type { AgentId } from "./pipelineStages";
import type { StageStatus } from "./usePipelineRun";

const IDLE_STAGES: Record<AgentId, StageStatus> = {
  orchestrator: "idle",
  data_engineering: "idle",
  kpi_semantic: "idle",
  bi_analyst: "idle",
  dashboard: "idle",
  auditor: "idle",
};

function mockPrefersReducedMotion(matches: boolean) {
  window.matchMedia = jest.fn().mockImplementation((query: string) => ({
    matches: matches && query === "(prefers-reduced-motion: reduce)",
    media: query,
    onchange: null,
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    addListener: jest.fn(),
    removeListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })) as unknown as typeof window.matchMedia;
}

const originalMatchMedia = window.matchMedia;

afterEach(() => {
  window.matchMedia = originalMatchMedia;
});

describe("PipelineGraph", () => {
  it("renders a traveling dot along the active stage's edge", () => {
    mockPrefersReducedMotion(false);
    const { container } = render(
      <PipelineGraph stages={{ ...IDLE_STAGES, kpi_semantic: "active" }} />
    );

    expect(container.querySelector("animateMotion")).toBeInTheDocument();
  });

  it("skips the traveling dot animation when the user prefers reduced motion", () => {
    mockPrefersReducedMotion(true);
    const { container } = render(
      <PipelineGraph stages={{ ...IDLE_STAGES, kpi_semantic: "active" }} />
    );

    expect(container.querySelector("animateMotion")).not.toBeInTheDocument();
  });

  it("shows the done label under a completed node", () => {
    mockPrefersReducedMotion(false);
    const { getByText } = render(
      <PipelineGraph stages={{ ...IDLE_STAGES, bi_analyst: "done" }} />
    );

    expect(getByText("✓ Analyzed")).toBeInTheDocument();
  });

  it("shows the error label under a failed node", () => {
    mockPrefersReducedMotion(false);
    const { getByText } = render(
      <PipelineGraph stages={{ ...IDLE_STAGES, dashboard: "error" }} />
    );

    expect(getByText("✗ Failed")).toBeInTheDocument();
  });
});

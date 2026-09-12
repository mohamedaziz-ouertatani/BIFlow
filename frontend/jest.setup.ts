import "@testing-library/jest-dom";

// recharts' ResponsiveContainer needs ResizeObserver, which jsdom doesn't implement.
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;

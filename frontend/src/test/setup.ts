import '@testing-library/jest-dom/vitest'

// jsdom does not implement ResizeObserver, which recharts (and most chart
// libraries) require. Provide a minimal no-op polyfill so chart components
// can render in tests without crashing.
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
;(globalThis as unknown as { ResizeObserver: typeof ResizeObserverMock }).ResizeObserver =
  ResizeObserverMock

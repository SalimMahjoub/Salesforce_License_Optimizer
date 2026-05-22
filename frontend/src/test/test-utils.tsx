import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import { type ReactElement, type ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'

interface WrapperOptions {
  /** Initial URL the in-memory router starts on. */
  route?: string
}

/**
 * Wraps a unit under test with the providers it expects in production:
 * QueryClient (no retries, no caching across tests) + a memory Router.
 *
 * Always create a FRESH QueryClient per render so cached responses from a
 * previous test cannot leak.
 */
export function renderWithProviders(
  ui: ReactElement,
  options: WrapperOptions & Omit<RenderOptions, 'wrapper'> = {},
) {
  const { route = '/', ...rest } = options
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  })

  function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[route]}>{children}</MemoryRouter>
      </QueryClientProvider>
    )
  }

  return { queryClient, ...render(ui, { wrapper: Wrapper, ...rest }) }
}

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { lazy, Suspense } from 'react'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { RequireAuth } from './components/auth/RequireAuth'
import { Layout } from './components/layout/Layout'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { Spinner } from './components/ui/Spinner'
import { ToastViewport } from './components/ui/Toast'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'

// Lazy-load secondary pages so the dashboard ships in the smallest bundle.
// First navigation to these routes triggers a chunk download (~few KB each).
const ZombiesPage = lazy(() =>
  import('./pages/ZombiesPage').then((m) => ({ default: m.ZombiesPage })),
)
const UsersPage = lazy(() =>
  import('./pages/UsersPage').then((m) => ({ default: m.UsersPage })),
)
const RecommendationsPage = lazy(() =>
  import('./pages/RecommendationsPage').then((m) => ({ default: m.RecommendationsPage })),
)
const ReportsPage = lazy(() =>
  import('./pages/ReportsPage').then((m) => ({ default: m.ReportsPage })),
)
const AlertsPage = lazy(() =>
  import('./pages/AlertsPage').then((m) => ({ default: m.AlertsPage })),
)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
})

function RouteFallback() {
  return (
    <div className="flex items-center justify-center py-24" aria-live="polite">
      <Spinner size="lg" />
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ErrorBoundary>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route
              path="/"
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route
                path="zombies"
                element={
                  <Suspense fallback={<RouteFallback />}>
                    <ZombiesPage />
                  </Suspense>
                }
              />
              <Route
                path="users"
                element={
                  <Suspense fallback={<RouteFallback />}>
                    <UsersPage />
                  </Suspense>
                }
              />
              <Route
                path="recommendations"
                element={
                  <Suspense fallback={<RouteFallback />}>
                    <RecommendationsPage />
                  </Suspense>
                }
              />
              <Route
                path="reports"
                element={
                  <Suspense fallback={<RouteFallback />}>
                    <ReportsPage />
                  </Suspense>
                }
              />
              <Route
                path="alerts"
                element={
                  <Suspense fallback={<RouteFallback />}>
                    <AlertsPage />
                  </Suspense>
                }
              />
              <Route
                path="*"
                element={
                  <div className="p-8 text-center text-gray-600">
                    <h2 className="text-2xl font-semibold">404</h2>
                    <p className="mt-2">Page introuvable.</p>
                  </div>
                }
              />
            </Route>
          </Routes>
        </BrowserRouter>
        <ToastViewport />
      </ErrorBoundary>
    </QueryClientProvider>
  )
}

export default App

import { useEffect } from 'react'
import { Outlet } from 'react-router-dom'
import { ErrorBoundary } from '../ui/ErrorBoundary'
import { useAppStore } from '../../stores/appStore'
import { useAuthStore } from '../../stores/authStore'
import { Header } from './Header'
import { Sidebar } from './Sidebar'

export function Layout() {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)
  const setCurrentOrg = useAppStore((s) => s.setCurrentOrg)
  const session = useAuthStore((s) => s.session)

  // Keep currentOrg in sync with the authenticated tenant so all API hooks
  // automatically scope to the correct org_id after login/logout.
  useEffect(() => {
    if (session?.tenantId) {
      setCurrentOrg(session.tenantId)
    }
  }, [session?.tenantId, setCurrentOrg])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Skip-to-content for keyboard users (WCAG 2.4.1) */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[60] focus:bg-primary-600 focus:text-white focus:px-4 focus:py-2 focus:rounded"
      >
        Aller au contenu principal
      </a>

      <Sidebar />

      <div
        className={
          'transition-all duration-300 ' +
          // Desktop: shift content right when sidebar is open. Mobile: never
          // shift — the sidebar is an overlay drawer there.
          (sidebarOpen ? 'lg:ml-64' : 'lg:ml-0')
        }
      >
        <Header />
        <main id="main-content" className="p-4 sm:p-6" tabIndex={-1}>
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}

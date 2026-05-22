import { LogOut, Menu } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { toast } from '../ui/Toast'
import { useAppStore } from '../../stores/appStore'
import { useAuthStore } from '../../stores/authStore'

export function Header() {
  const toggleSidebar = useAppStore((s) => s.toggleSidebar)
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)
  const session = useAuthStore((s) => s.session)
  const logout = useAuthStore((s) => s.logout)
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    toast.success('Déconnexion', 'À bientôt.')
    navigate('/login', { replace: true })
  }

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center px-4 sm:px-6 sticky top-0 z-30">
      <button
        type="button"
        onClick={toggleSidebar}
        className="p-2 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label={sidebarOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
        aria-expanded={sidebarOpen}
        aria-controls="primary-navigation"
      >
        <Menu className="w-5 h-5 text-gray-600" />
      </button>

      <div className="ml-auto flex items-center gap-3 sm:gap-4">
        {session && (
          <>
            <div className="hidden sm:block text-sm text-gray-700 max-w-[240px] truncate">
              <span className="text-gray-500">Connecté :</span>{' '}
              <strong title={session.email}>{session.email}</strong>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors inline-flex items-center gap-1 text-sm text-gray-600 focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label="Se déconnecter"
            >
              <LogOut className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </>
        )}
      </div>
    </header>
  )
}

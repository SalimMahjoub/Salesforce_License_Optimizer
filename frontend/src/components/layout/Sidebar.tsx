import { NavLink } from 'react-router-dom'
import {
  BarChart3,
  FileText,
  LayoutDashboard,
  Settings,
  ShieldAlert,
  Skull,
  Users,
  X,
} from 'lucide-react'
import { cn } from '../../lib/utils'
import { useAppStore } from '../../stores/appStore'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Zombies', href: '/zombies', icon: Skull },
  { name: 'Utilisateurs', href: '/users', icon: Users },
  { name: 'Recommandations', href: '/recommendations', icon: FileText },
  { name: 'Rapport CFO', href: '/reports', icon: BarChart3 },
  { name: 'Alertes sécurité', href: '/alerts', icon: ShieldAlert },
  { name: 'Paramètres', href: '/settings', icon: Settings },
]

/**
 * Sidebar — desktop fixed + mobile drawer. On screens < lg, it slides in
 * from the left with a backdrop; tapping a link auto-closes on mobile.
 */
export function Sidebar() {
  const sidebarOpen = useAppStore((s) => s.sidebarOpen)
  const toggleSidebar = useAppStore((s) => s.toggleSidebar)

  return (
    <>
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Fermer le menu"
          className="fixed inset-0 z-40 bg-gray-900/50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      <nav
        aria-label="Navigation principale"
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200',
          'transition-transform duration-300 ease-in-out',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        <div className="flex h-16 items-center justify-between px-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-primary-600">SF License Optimizer</h1>
          <button
            type="button"
            onClick={toggleSidebar}
            className="lg:hidden p-1 text-gray-500 hover:text-gray-700"
            aria-label="Fermer le menu"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <ul className="flex-1 space-y-1 px-3 py-4">
          {navigation.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.href}
                onClick={() => {
                  // Auto-close on mobile after navigation
                  if (window.innerWidth < 1024) toggleSidebar()
                }}
                className={({ isActive }) =>
                  cn(
                    'flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors',
                    'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-1',
                    isActive
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-700 hover:bg-gray-50',
                  )
                }
              >
                <item.icon className="w-5 h-5 mr-3" aria-hidden="true" />
                {item.name}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </>
  )
}

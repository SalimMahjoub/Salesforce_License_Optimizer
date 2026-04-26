import { Menu } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'

export function Header() {
  const { toggleSidebar } = useAppStore()

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6">
      <button
        onClick={toggleSidebar}
        className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        aria-label="Toggle sidebar"
      >
        <Menu className="w-5 h-5 text-gray-600" />
      </button>
      
      <div className="ml-auto flex items-center space-x-4">
        <div className="text-sm text-gray-600">
          Demo Account
        </div>
      </div>
    </header>
  )
}


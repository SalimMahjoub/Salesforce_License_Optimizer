import { Badge } from '../ui/Badge'
import { formatDate } from '../../lib/utils'
import type { ClassifiedUser, UserCategory } from '../../lib/types'

interface UsersTableProps {
  users: ClassifiedUser[]
  loading?: boolean
  emptyMessage?: string
}

const CATEGORY_VARIANT: Record<UserCategory, 'success' | 'default' | 'warning' | 'danger'> = {
  efficient: 'success',
  optimizable: 'default',
  underutilized: 'warning',
  inactive: 'danger',
}

const CATEGORY_LABEL: Record<UserCategory, string> = {
  efficient: 'Efficace',
  optimizable: 'Optimisable',
  underutilized: 'Sous-utilisé',
  inactive: 'Inactif',
}

export function UsersTable({
  users,
  loading = false,
  emptyMessage = 'Aucun utilisateur',
}: UsersTableProps) {
  if (loading) {
    return <div className="p-8 text-center text-gray-500" aria-live="polite">Chargement…</div>
  }

  if (!users.length) {
    return <div className="p-8 text-center text-gray-500">{emptyMessage}</div>
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Utilisateur
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Licence
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Score
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Catégorie
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Dernière connexion
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {users.map((user) => (
            <tr key={user.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 whitespace-nowrap">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {user.full_name ?? user.username}
                  </div>
                  <div className="text-sm text-gray-500">{user.email ?? user.username}</div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">{user.license_type}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-semibold text-gray-900">
                  {user.activity_score}/100
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Badge variant={CATEGORY_VARIANT[user.category]}>
                  {CATEGORY_LABEL[user.category]}
                </Badge>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {user.last_login_date ? formatDate(user.last_login_date) : 'Jamais'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

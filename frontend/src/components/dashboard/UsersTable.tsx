import { Badge } from '../ui/Badge'
import { formatDate } from '../../lib/utils'

interface User {
  id: string
  username: string
  email: string
  license_type: string
  activity_score: number
  category: string
  last_login_date: string | null
}

interface UsersTableProps {
  users: User[]
  loading?: boolean
}

export function UsersTable({ users, loading = false }: UsersTableProps) {
  const getCategoryVariant = (category: string) => {
    switch (category) {
      case 'EFFICIENT':
        return 'success'
      case 'OPTIMIZABLE':
        return 'default'
      case 'UNDERUTILIZED':
        return 'warning'
      case 'INACTIVE':
        return 'danger'
      default:
        return 'default'
    }
  }

  const getCategoryLabel = (category: string) => {
    switch (category) {
      case 'EFFICIENT':
        return 'Efficace'
      case 'OPTIMIZABLE':
        return 'Optimisable'
      case 'UNDERUTILIZED':
        return 'Sous-utilisé'
      case 'INACTIVE':
        return 'Inactif'
      default:
        return category
    }
  }

  if (loading) {
    return <div className="p-8 text-center text-gray-500">Chargement...</div>
  }

  if (!users.length) {
    return <div className="p-8 text-center text-gray-500">Aucun utilisateur</div>
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
                  <div className="text-sm font-medium text-gray-900">{user.username}</div>
                  <div className="text-sm text-gray-500">{user.email}</div>
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm text-gray-900">{user.license_type}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-semibold text-gray-900">{user.activity_score}/100</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <Badge variant={getCategoryVariant(user.category)}>
                  {getCategoryLabel(user.category)}
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


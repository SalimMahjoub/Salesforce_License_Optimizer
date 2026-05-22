import { useState } from 'react'
import { Users as UsersIcon } from 'lucide-react'
import { UsersTable } from '../components/dashboard/UsersTable'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { TableRowsSkeleton } from '../components/ui/Skeleton'
import { useUsers } from '../hooks/useAnalysis'
import type { UserCategory } from '../lib/types'
import { useAppStore } from '../stores/appStore'

const CATEGORIES: { value: UserCategory | ''; label: string }[] = [
  { value: '', label: 'Tous' },
  { value: 'inactive', label: 'Inactifs' },
  { value: 'underutilized', label: 'Sous-utilisés' },
  { value: 'optimizable', label: 'Optimisables' },
  { value: 'efficient', label: 'Efficaces' },
]

export function UsersPage() {
  const orgId = useAppStore((s) => s.currentOrg)
  const [category, setCategory] = useState<UserCategory | ''>('')
  const [page, setPage] = useState(1)
  const pageSize = 50
  const { data, isLoading, isError, error } = useUsers(orgId, {
    category: category || undefined,
    page,
    pageSize,
  })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Utilisateurs</h1>
        <p className="text-gray-600 mt-1">
          {data?.total ?? 0} utilisateurs classifiés sur l'org{' '}
          <code className="bg-gray-100 px-1.5 py-0.5 rounded">{orgId}</code>.
        </p>
      </header>

      {isError && (
        <Card>
          <div className="p-4 text-sm text-danger-700 bg-danger-50 rounded">
            Erreur : {(error as Error).message}
          </div>
        </Card>
      )}

      <Card title="Filtres">
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c.value || 'all'}
              type="button"
              className={`btn ${category === c.value ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => {
                setCategory(c.value)
                setPage(1)
              }}
            >
              {c.label}
            </button>
          ))}
        </div>
      </Card>

      <Card title={`Page ${page} / ${totalPages}`}>
        {isLoading ? (
          <TableRowsSkeleton rows={10} />
        ) : !data?.users.length ? (
          <EmptyState
            icon={<UsersIcon className="w-6 h-6" />}
            title="Aucun utilisateur"
            description="Ce filtre ne renvoie aucun utilisateur sur cette org."
          />
        ) : (
          <UsersTable users={data.users} />
        )}

        <div className="flex items-center justify-between mt-4">
          <button
            className="btn btn-secondary"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Précédent
          </button>
          <span className="text-sm text-gray-600">
            {data?.users.length ?? 0} affichés sur {data?.total ?? 0}
          </span>
          <button
            className="btn btn-secondary"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Suivant
          </button>
        </div>
      </Card>
    </div>
  )
}

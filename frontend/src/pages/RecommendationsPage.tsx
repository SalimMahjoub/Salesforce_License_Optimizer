import { useState } from 'react'
import { DollarSign, ListChecks, Sparkles } from 'lucide-react'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { StatGridSkeleton, TableRowsSkeleton } from '../components/ui/Skeleton'
import { StatCard } from '../components/ui/StatCard'
import { useRecommendations } from '../hooks/useAnalysis'
import { useAppStore } from '../stores/appStore'
import type { RecommendationPriority } from '../lib/types'
import { formatCurrency } from '../lib/utils'

const PRIORITY_VARIANT: Record<RecommendationPriority, 'danger' | 'warning' | 'default' | 'success'> = {
  CRITICAL: 'danger',
  HIGH: 'warning',
  MEDIUM: 'default',
  LOW: 'success',
}

const PRIORITY_LABEL: Record<RecommendationPriority, string> = {
  CRITICAL: 'Critique',
  HIGH: 'Haute',
  MEDIUM: 'Moyenne',
  LOW: 'Basse',
}

export function RecommendationsPage() {
  const orgId = useAppStore((s) => s.currentOrg)
  const [priority, setPriority] = useState<RecommendationPriority | ''>('')
  const [page, setPage] = useState(1)
  const { data, isLoading, isError, error } = useRecommendations(orgId, {
    priority: priority || undefined,
    page,
    pageSize: 50,
  })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Recommandations</h1>
        <p className="text-gray-600 mt-1">
          {data?.total ?? 0} actions identifiées pour réduire le coût des licences.
        </p>
      </header>

      {isError && (
        <Card>
          <div className="p-4 text-sm text-danger-700 bg-danger-50 rounded">
            Erreur : {(error as Error).message}
          </div>
        </Card>
      )}

      {isLoading ? (
        <StatGridSkeleton count={3} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title="Total recommandations"
            value={data?.total ?? 0}
            icon={<ListChecks className="w-6 h-6 text-primary-600" />}
          />
          <StatCard
            title="Économies mensuelles"
            value={Number(data?.total_monthly_savings ?? 0)}
            format="currency"
            icon={<DollarSign className="w-6 h-6 text-success-600" />}
          />
          <StatCard
            title="Économies annuelles"
            value={Number(data?.total_annual_savings ?? 0)}
            format="currency"
            icon={<DollarSign className="w-6 h-6 text-success-600" />}
          />
        </div>
      )}

      <Card title="Filtres">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className={`btn ${priority === '' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => {
              setPriority('')
              setPage(1)
            }}
          >
            Toutes
          </button>
          {(['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((p) => (
            <button
              key={p}
              type="button"
              className={`btn ${priority === p ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => {
                setPriority(p)
                setPage(1)
              }}
            >
              {PRIORITY_LABEL[p]}
            </button>
          ))}
        </div>
      </Card>

      <Card title={`Page ${page} / ${totalPages}`}>
        {isLoading ? (
          <TableRowsSkeleton rows={10} />
        ) : data?.recommendations.length === 0 ? (
          <EmptyState
            icon={<Sparkles className="w-6 h-6" />}
            title="Aucune recommandation"
            description="Pour ce filtre, aucune action n'est nécessaire. Tout est optimal."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Priorité</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Utilisateur</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Licence</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Action</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">€/mois</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data?.recommendations.map((rec) => (
                  <tr key={`${rec.user_id}-${rec.title}`} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Badge variant={PRIORITY_VARIANT[rec.priority]}>
                        {PRIORITY_LABEL[rec.priority]}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm">{rec.username}</td>
                    <td className="px-4 py-3 text-sm">{rec.license_type}</td>
                    <td className="px-4 py-3 text-sm font-medium">{rec.type}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{rec.title}</td>
                    <td className="px-4 py-3 text-sm text-right font-semibold text-success-700">
                      {formatCurrency(rec.monthly_savings)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
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
            {data?.recommendations.length ?? 0} affichées sur {data?.total ?? 0}
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

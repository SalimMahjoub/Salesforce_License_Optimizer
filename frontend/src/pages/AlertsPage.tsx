import { ShieldAlert, ShieldCheck } from 'lucide-react'
import { Badge } from '../components/ui/Badge'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { StatGridSkeleton, TableRowsSkeleton } from '../components/ui/Skeleton'
import { StatCard } from '../components/ui/StatCard'
import { useAlerts } from '../hooks/useAnalysis'
import type { AlertSeverity } from '../lib/types'
import { useAppStore } from '../stores/appStore'

const SEVERITY_VARIANT: Record<AlertSeverity, 'danger' | 'warning' | 'default' | 'success'> = {
  CRITICAL: 'danger',
  HIGH: 'warning',
  MEDIUM: 'default',
  LOW: 'success',
}

const SEVERITY_LABEL: Record<AlertSeverity, string> = {
  CRITICAL: 'Critique',
  HIGH: 'Élevée',
  MEDIUM: 'Moyenne',
  LOW: 'Basse',
}

export function AlertsPage() {
  const orgId = useAppStore((s) => s.currentOrg)
  const { data, isLoading, isError, error } = useAlerts(orgId)

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Alertes de sécurité</h1>
        <p className="text-gray-600 mt-1">
          Risques détectés par le moniteur de permissions : comptes admin orphelins,
          licences à haut privilège inutilisées, dormance prolongée.
        </p>
      </header>

      {isError && (
        <Card>
          <div className="p-4 text-sm text-danger-700 bg-danger-50 rounded" role="alert">
            Erreur : {(error as Error).message}
          </div>
        </Card>
      )}

      {isLoading ? (
        <StatGridSkeleton />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard
            title="Alertes totales"
            value={data?.total ?? 0}
            icon={<ShieldAlert className="w-6 h-6 text-danger-600" />}
          />
          {(['CRITICAL', 'HIGH', 'MEDIUM'] as const).map((sev) => (
            <StatCard
              key={sev}
              title={SEVERITY_LABEL[sev]}
              value={data?.by_severity[sev] ?? 0}
            />
          ))}
        </div>
      )}

      <Card title="Détail">
        {isLoading ? (
          <TableRowsSkeleton rows={8} />
        ) : !data?.alerts.length ? (
          <EmptyState
            icon={<ShieldCheck className="w-6 h-6" />}
            title="Aucune alerte"
            description="L'org est saine côté permissions inactives. 🎉"
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Sévérité
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Utilisateur
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Règle
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Description
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                    Action recommandée
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data.alerts.map((a, i) => (
                  <tr key={`${a.user_id}-${a.permission}-${i}`} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Badge variant={SEVERITY_VARIANT[a.severity]}>
                        {SEVERITY_LABEL[a.severity]}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-sm">{a.username}</td>
                    <td className="px-4 py-3 text-xs font-mono text-gray-600">
                      {a.permission}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{a.description}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{a.recommended_action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

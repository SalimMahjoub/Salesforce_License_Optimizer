import { DollarSign, Skull } from 'lucide-react'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { StatGridSkeleton, TableRowsSkeleton } from '../components/ui/Skeleton'
import { StatCard } from '../components/ui/StatCard'
import { UsersTable } from '../components/dashboard/UsersTable'
import { useZombies } from '../hooks/useAnalysis'
import { useAppStore } from '../stores/appStore'

export function ZombiesPage() {
  const orgId = useAppStore((s) => s.currentOrg)
  const { data, isLoading, isError, error } = useZombies(orgId)

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Utilisateurs zombies</h1>
        <p className="text-gray-600 mt-1">
          Licences inactives (catégorie <strong>INACTIVE</strong>) — candidats prioritaires
          à désactivation ou downgrade.
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
        <StatGridSkeleton count={3} />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title="Zombies détectés"
            value={data?.zombie_count ?? 0}
            icon={<Skull className="w-6 h-6 text-danger-600" />}
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

      <Card title="Liste détaillée">
        {isLoading ? (
          <TableRowsSkeleton rows={10} />
        ) : !data?.users.length ? (
          <EmptyState
            icon={<Skull className="w-6 h-6" />}
            title="Aucun zombie détecté"
            description="Bravo — l'org est saine sur la dimension activité."
          />
        ) : (
          <UsersTable users={data.users} />
        )}
      </Card>
    </div>
  )
}

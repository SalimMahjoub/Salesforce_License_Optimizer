import { AlertTriangle, DollarSign, RefreshCw, Skull, TrendingUp, Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { CategoryDonut, CategoryLegend } from '../components/charts/CategoryDonut'
import { SavingsGauge } from '../components/charts/SavingsGauge'
import { UsersTable } from '../components/dashboard/UsersTable'
import { Card } from '../components/ui/Card'
import { EmptyState } from '../components/ui/EmptyState'
import { Skeleton, StatGridSkeleton } from '../components/ui/Skeleton'
import { Spinner } from '../components/ui/Spinner'
import { StatCard } from '../components/ui/StatCard'
import { toast } from '../components/ui/Toast'
import { useDashboard, useRefreshAnalysis, useZombies } from '../hooks/useAnalysis'
import { formatCurrency } from '../lib/utils'
import { useAppStore } from '../stores/appStore'

export function DashboardPage() {
  const orgId = useAppStore((s) => s.currentOrg)
  const dashboard = useDashboard(orgId)
  const zombies = useZombies(orgId)
  const refresh = useRefreshAnalysis(orgId)

  const kpis = dashboard.data
  const noData = !dashboard.isLoading && (!kpis || kpis.total_users === 0)

  function handleRefresh() {
    refresh.mutate(undefined, {
      onSuccess: () => toast.success('Analyse relancée', 'Les données sont à jour.'),
      onError: (err) => toast.error('Échec du refresh', (err as Error).message),
    })
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Org{' '}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm">{orgId}</code> —
            optimisation des licences Salesforce
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary inline-flex items-center gap-2 self-start"
          onClick={handleRefresh}
          disabled={refresh.isPending}
          aria-label="Relancer l'analyse"
        >
          {refresh.isPending ? (
            <Spinner size="sm" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          {refresh.isPending ? 'Analyse…' : 'Relancer l’analyse'}
        </button>
      </header>

      {dashboard.isError && (
        <Card>
          <div className="p-4 text-sm text-danger-700 bg-danger-50 rounded" role="alert">
            Impossible de charger les KPIs : {(dashboard.error as Error).message}
          </div>
        </Card>
      )}

      {/* KPI grid */}
      {dashboard.isLoading ? (
        <StatGridSkeleton />
      ) : noData ? (
        <Card>
          <EmptyState
            icon={<Users className="w-6 h-6" />}
            title="Aucune donnée disponible"
            description="L'org n'a pas encore été analysée ou ne contient aucun utilisateur."
            action={
              <button type="button" className="btn btn-primary" onClick={handleRefresh}>
                Lancer une première analyse
              </button>
            }
          />
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Utilisateurs analysés"
              value={kpis!.total_users}
              format="number"
              icon={<Users className="w-6 h-6 text-primary-600" />}
            />
            <StatCard
              title="Économies mensuelles"
              value={Number(kpis!.total_monthly_savings)}
              format="currency"
              icon={<DollarSign className="w-6 h-6 text-success-600" />}
            />
            <StatCard
              title="Recommandations"
              value={kpis!.recommendations_count}
              format="number"
              icon={<AlertTriangle className="w-6 h-6 text-warning-600" />}
            />
            <StatCard
              title="Économies annuelles"
              value={Number(kpis!.total_annual_savings)}
              format="currency"
              icon={<TrendingUp className="w-6 h-6 text-primary-600" />}
            />
          </div>

          {/* Two-column: donut + gauge / details */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card title="Répartition par catégorie">
              <div className="flex flex-col md:flex-row items-center gap-6">
                <CategoryDonut counts={kpis!.counts_by_category} />
                <div className="flex-1 min-w-0">
                  <CategoryLegend counts={kpis!.counts_by_category} />
                </div>
              </div>
            </Card>

            <Card title="Taux d'économies">
              <div className="flex flex-col items-center justify-center h-full py-2">
                <SavingsGauge rate={kpis!.savings_rate} />
                <p className="text-xs text-gray-500 text-center mt-3 max-w-[200px]">
                  Part du coût mensuel actuel ({formatCurrency(kpis!.total_monthly_cost)})
                  qui peut être économisée.
                </p>
              </div>
            </Card>

            <Card
              title="Zombies"
              subtitle={`${kpis!.zombie_count} utilisateurs inactifs`}
              action={
                <Link to="/zombies" className="text-sm text-primary-600 hover:underline">
                  Voir tous →
                </Link>
              }
            >
              <div className="flex items-center gap-4 p-2">
                <div className="p-4 bg-danger-50 rounded-full text-danger-600">
                  <Skull className="w-8 h-8" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-gray-900">
                    {formatCurrency(kpis!.zombie_monthly_savings)}
                  </div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider">
                    Économies mensuelles
                  </div>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Soit{' '}
                <strong className="text-success-700">
                  {formatCurrency(Number(kpis!.zombie_monthly_savings) * 12)}
                </strong>{' '}
                d'économies annuelles sur les comptes inactifs.
              </p>
            </Card>
          </div>

          {/* Zombie preview table */}
          <Card
            title="Zombies prioritaires"
            subtitle="Top 10 utilisateurs inactifs à désactiver/downgrade"
            action={
              <Link to="/zombies" className="text-sm text-primary-600 hover:underline">
                Voir tous →
              </Link>
            }
          >
            {zombies.isLoading ? (
              <div className="space-y-2 p-2">
                {Array.from({ length: 5 }, (_, i) => (
                  <Skeleton key={i} variant="row" />
                ))}
              </div>
            ) : zombies.data && zombies.data.users.length > 0 ? (
              <UsersTable users={zombies.data.users.slice(0, 10)} />
            ) : (
              <EmptyState
                icon={<Skull className="w-6 h-6" />}
                title="Aucun zombie détecté"
                description="L'org ne contient pas d'utilisateurs inactifs. 🎉"
              />
            )}
          </Card>
        </>
      )}
    </div>
  )
}

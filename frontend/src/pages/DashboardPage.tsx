import { Users, DollarSign, AlertTriangle, TrendingUp } from 'lucide-react'
import { StatCard } from '../components/ui/StatCard'
import { Card } from '../components/ui/Card'
import { UsersTable } from '../components/dashboard/UsersTable'

export function DashboardPage() {
  // Mock data - will be replaced with real API calls
  const stats = {
    totalUsers: 150,
    monthlySavings: 12500,
    recommendations: 42,
    efficiency: 68,
  }

  const mockUsers = [
    {
      id: '1',
      username: 'john.doe@company.com',
      email: 'john.doe@company.com',
      license_type: 'Sales Cloud',
      activity_score: 85,
      category: 'EFFICIENT',
      last_login_date: '2024-02-08',
    },
    {
      id: '2',
      username: 'jane.smith@company.com',
      email: 'jane.smith@company.com',
      license_type: 'Platform',
      activity_score: 35,
      category: 'UNDERUTILIZED',
      last_login_date: '2024-01-15',
    },
    {
      id: '3',
      username: 'bob.wilson@company.com',
      email: 'bob.wilson@company.com',
      license_type: 'Service Cloud',
      activity_score: 15,
      category: 'INACTIVE',
      last_login_date: '2023-11-20',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">
          Vue d'ensemble de l'optimisation des licences Salesforce
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Utilisateurs totaux"
          value={stats.totalUsers}
          format="number"
          change={5.2}
          changeLabel="vs mois dernier"
          icon={<Users className="w-6 h-6 text-primary-600" />}
        />
        <StatCard
          title="Économies mensuelles"
          value={stats.monthlySavings}
          format="currency"
          change={12.8}
          changeLabel="vs mois dernier"
          icon={<DollarSign className="w-6 h-6 text-success-600" />}
        />
        <StatCard
          title="Recommandations"
          value={stats.recommendations}
          format="number"
          icon={<AlertTriangle className="w-6 h-6 text-warning-600" />}
        />
        <StatCard
          title="Efficacité moyenne"
          value={stats.efficiency}
          format="percentage"
          change={3.4}
          changeLabel="vs mois dernier"
          icon={<TrendingUp className="w-6 h-6 text-primary-600" />}
        />
      </div>

      {/* Users Table */}
      <Card title="Utilisateurs récents" subtitle="Aperçu des derniers utilisateurs analysés">
        <UsersTable users={mockUsers} />
      </Card>

      {/* Quick Actions */}
      <Card title="Actions rapides">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn btn-primary">
            Lancer une analyse
          </button>
          <button className="btn btn-secondary">
            Générer un rapport
          </button>
          <button className="btn btn-secondary">
            Exporter les données
          </button>
        </div>
      </Card>
    </div>
  )
}


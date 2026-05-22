import { useState, type FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { Card } from '../components/ui/Card'
import { api } from '../lib/api'
import { useAuthStore } from '../stores/authStore'
import { useAppStore } from '../stores/appStore'

interface LoginResponse {
  access_token: string
  token_type: string
  tenant_id: string
  email: string
}

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const setSession = useAuthStore((s) => s.setSession)
  const setCurrentOrg = useAppStore((s) => s.setCurrentOrg)
  const [email, setEmail] = useState('demo@uprizon.io')
  const [password, setPassword] = useState('demo-password')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const redirectTo = (location.state as { from?: string } | null)?.from ?? '/dashboard'

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      // OAuth2PasswordRequestForm expects application/x-www-form-urlencoded
      const params = new URLSearchParams()
      params.set('username', email)
      params.set('password', password)
      const { data } = await api.post<LoginResponse>('/api/v1/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      setSession({ token: data.access_token, email: data.email, tenantId: data.tenant_id })
      setCurrentOrg(data.tenant_id)
      navigate(redirectTo, { replace: true })
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
        (err as Error).message
      setError(typeof message === 'string' ? message : 'Échec de connexion')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Card>
          <div className="text-center mb-6">
            <h1 className="text-2xl font-bold text-primary-600">SF License Optimizer</h1>
            <p className="text-gray-600 text-sm mt-1">Connectez-vous pour accéder au dashboard</p>
          </div>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Mot de passe
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && (
              <div className="p-3 text-sm text-danger-700 bg-danger-50 rounded" role="alert">
                {error}
              </div>
            )}
            <button
              type="submit"
              className="btn btn-primary w-full"
              disabled={loading}
            >
              {loading ? 'Connexion…' : 'Se connecter'}
            </button>
          </form>
          <p className="text-xs text-gray-500 text-center mt-4">
            Démo : <code>demo@uprizon.io</code> / <code>demo-password</code>
          </p>
        </Card>
      </div>
    </div>
  )
}

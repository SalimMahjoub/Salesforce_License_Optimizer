import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import type {
  ActionPlan,
  DashboardKPIs,
  RecommendationPriority,
  RecommendationsListResponse,
  RecommendationType,
  SecurityAlertsResponse,
  UserCategory,
  UsersListResponse,
  ZombieReport,
} from '../lib/types'

export const analysisKeys = {
  all: ['analysis'] as const,
  dashboard: (orgId: string) => ['analysis', orgId, 'dashboard'] as const,
  zombies: (orgId: string) => ['analysis', orgId, 'zombies'] as const,
  users: (orgId: string, category?: UserCategory, page = 1) =>
    ['analysis', orgId, 'users', { category, page }] as const,
}

export function useDashboard(orgId: string) {
  return useQuery({
    queryKey: analysisKeys.dashboard(orgId),
    queryFn: async () => {
      const { data } = await api.get<DashboardKPIs>(`/api/v1/analysis/${orgId}/dashboard`)
      return data
    },
    enabled: Boolean(orgId),
  })
}

export function useZombies(orgId: string) {
  return useQuery({
    queryKey: analysisKeys.zombies(orgId),
    queryFn: async () => {
      const { data } = await api.get<ZombieReport>(`/api/v1/analysis/${orgId}/zombies`)
      return data
    },
    enabled: Boolean(orgId),
  })
}

interface UseUsersOptions {
  category?: UserCategory
  page?: number
  pageSize?: number
}

export function useUsers(orgId: string, options: UseUsersOptions = {}) {
  const { category, page = 1, pageSize = 50 } = options
  return useQuery({
    queryKey: analysisKeys.users(orgId, category, page),
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize }
      if (category) params.category = category
      const { data } = await api.get<UsersListResponse>(
        `/api/v1/analysis/${orgId}/users`,
        { params },
      )
      return data
    },
    enabled: Boolean(orgId),
    placeholderData: (previous) => previous,
  })
}

interface UseRecommendationsOptions {
  priority?: RecommendationPriority
  type?: RecommendationType
  page?: number
  pageSize?: number
}

export function useRecommendations(orgId: string, options: UseRecommendationsOptions = {}) {
  const { priority, type, page = 1, pageSize = 50 } = options
  return useQuery({
    queryKey: ['analysis', orgId, 'recommendations', { priority, type, page }],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: pageSize }
      if (priority) params.priority = priority
      if (type) params.type = type
      const { data } = await api.get<RecommendationsListResponse>(
        `/api/v1/recommendations/${orgId}`,
        { params },
      )
      return data
    },
    enabled: Boolean(orgId),
    placeholderData: (previous) => previous,
  })
}

export function useCfoPlan(orgId: string, orgName = 'Organization') {
  return useQuery({
    queryKey: ['analysis', orgId, 'cfo-plan', orgName],
    queryFn: async () => {
      const { data } = await api.get<ActionPlan>(
        `/api/v1/reports/${orgId}/cfo-plan`,
        { params: { org_name: orgName } },
      )
      return data
    },
    enabled: Boolean(orgId),
  })
}

export function useAlerts(orgId: string) {
  return useQuery({
    queryKey: ['analysis', orgId, 'alerts'],
    queryFn: async () => {
      const { data } = await api.get<SecurityAlertsResponse>(`/api/v1/alerts/${orgId}`)
      return data
    },
    enabled: Boolean(orgId),
  })
}

export function useRefreshAnalysis(orgId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/api/v1/analysis/${orgId}/refresh`)
      return data
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['analysis', orgId] })
    },
  })
}

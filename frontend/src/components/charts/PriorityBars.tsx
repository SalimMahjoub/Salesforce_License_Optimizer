import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { RecommendationPriority } from '../../lib/types'

interface PriorityBarsProps {
  counts: Record<string, number>
  height?: number
}

const PRIORITY_ORDER: RecommendationPriority[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
const PRIORITY_LABEL: Record<RecommendationPriority, string> = {
  CRITICAL: 'Critique',
  HIGH: 'Haute',
  MEDIUM: 'Moyenne',
  LOW: 'Basse',
}
const PRIORITY_COLOR: Record<RecommendationPriority, string> = {
  CRITICAL: '#dc2626',
  HIGH: '#ea580c',
  MEDIUM: '#0284c7',
  LOW: '#16a34a',
}

export function PriorityBars({ counts, height = 200 }: PriorityBarsProps) {
  const data = PRIORITY_ORDER.map((p) => ({
    priority: PRIORITY_LABEL[p],
    count: counts[p] ?? 0,
    fill: PRIORITY_COLOR[p],
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
        <XAxis dataKey="priority" tick={{ fontSize: 12 }} stroke="#6b7280" />
        <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" allowDecimals={false} />
        <Tooltip
          formatter={(value: number) => [value.toLocaleString('fr-FR'), 'Recommandations']}
          cursor={{ fill: 'rgba(229, 231, 235, 0.4)' }}
        />
        <Bar dataKey="count" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

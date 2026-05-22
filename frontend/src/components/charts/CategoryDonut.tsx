import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import type { UserCategory } from '../../lib/types'

interface CategoryDonutProps {
  counts: Record<UserCategory, number>
  size?: number
}

const COLORS: Record<UserCategory, string> = {
  inactive: '#dc2626',       // danger-600
  underutilized: '#ea580c',  // orange-600
  optimizable: '#0284c7',    // primary-600
  efficient: '#16a34a',      // success-600
}

const LABELS: Record<UserCategory, string> = {
  inactive: 'Inactifs',
  underutilized: 'Sous-utilisés',
  optimizable: 'Optimisables',
  efficient: 'Efficaces',
}

/** Donut chart for the user-category distribution. Centered total in the hole. */
export function CategoryDonut({ counts, size = 240 }: CategoryDonutProps) {
  const data = (Object.keys(LABELS) as UserCategory[]).map((cat) => ({
    name: LABELS[cat],
    value: counts[cat] ?? 0,
    color: COLORS[cat],
    cat,
  }))
  const total = data.reduce((s, d) => s + d.value, 0)

  return (
    <div className="relative inline-block" style={{ width: size, height: size }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius="60%"
            outerRadius="90%"
            paddingAngle={2}
            stroke="none"
          >
            {data.map((entry) => (
              <Cell key={entry.cat} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number, name: string) => [
              `${value} (${total ? ((value / total) * 100).toFixed(1) : 0} %)`,
              name,
            ]}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <div className="text-3xl font-bold text-gray-900">{total.toLocaleString('fr-FR')}</div>
        <div className="text-xs text-gray-500 uppercase tracking-wider">Total</div>
      </div>
    </div>
  )
}

/** Legend compagnon de CategoryDonut. */
export function CategoryLegend({ counts }: { counts: Record<UserCategory, number> }) {
  const total = (Object.values(counts) as number[]).reduce((s, n) => s + n, 0)
  return (
    <ul className="space-y-2">
      {(Object.keys(LABELS) as UserCategory[]).map((cat) => {
        const n = counts[cat] ?? 0
        const pct = total ? (n / total) * 100 : 0
        return (
          <li key={cat} className="flex items-center justify-between text-sm">
            <span className="flex items-center gap-2">
              <span
                aria-hidden="true"
                className="inline-block w-3 h-3 rounded-sm"
                style={{ backgroundColor: COLORS[cat] }}
              />
              {LABELS[cat]}
            </span>
            <span className="tabular-nums text-gray-700">
              <strong>{n}</strong>{' '}
              <span className="text-gray-500">({pct.toFixed(1)} %)</span>
            </span>
          </li>
        )
      })}
    </ul>
  )
}

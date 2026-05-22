import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'

interface SavingsGaugeProps {
  /** 0 .. 1 — share of monthly cost that is recoverable. */
  rate: number
  size?: number
}

/** Half-donut gauge for savings rate. Color shifts based on intensity. */
export function SavingsGauge({ rate, size = 200 }: SavingsGaugeProps) {
  const pct = Math.max(0, Math.min(1, rate))
  // Color thresholds: green > 50 %, amber > 20 %, red otherwise.
  const fill = pct > 0.5 ? '#16a34a' : pct > 0.2 ? '#ea580c' : '#dc2626'
  const data = [
    { name: 'value', value: pct },
    { name: 'rest', value: 1 - pct },
  ]
  return (
    <div className="relative inline-block" style={{ width: size, height: size / 2 + 16 }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            startAngle={180}
            endAngle={0}
            innerRadius="65%"
            outerRadius="100%"
            stroke="none"
            cy="100%"
          >
            <Cell fill={fill} />
            <Cell fill="#e5e7eb" />
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-x-0 bottom-0 flex flex-col items-center pb-1">
        <div className="text-2xl font-bold text-gray-900">{(pct * 100).toFixed(1)} %</div>
        <div className="text-xs text-gray-500 uppercase tracking-wider">Économies</div>
      </div>
    </div>
  )
}

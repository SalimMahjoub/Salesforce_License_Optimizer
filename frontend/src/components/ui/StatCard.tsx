import { ReactNode } from 'react'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { Card } from './Card'
import { cn, formatCurrency, formatNumber } from '../../lib/utils'

interface StatCardProps {
  title: string
  value: number
  format?: 'number' | 'currency' | 'percentage'
  change?: number
  changeLabel?: string
  icon?: ReactNode
  loading?: boolean
}

export function StatCard({
  title,
  value,
  format = 'number',
  change,
  changeLabel,
  icon,
  loading = false,
}: StatCardProps) {
  const formatValue = () => {
    if (loading) return '...'
    
    switch (format) {
      case 'currency':
        return formatCurrency(value)
      case 'percentage':
        return `${value.toFixed(1)}%`
      default:
        return formatNumber(value)
    }
  }

  const isPositive = change !== undefined && change > 0
  const isNegative = change !== undefined && change < 0

  return (
    <Card className="relative overflow-hidden">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{formatValue()}</p>
          
          {change !== undefined && (
            <div className="flex items-center mt-2">
              {isPositive && <TrendingUp className="w-4 h-4 text-success-600 mr-1" />}
              {isNegative && <TrendingDown className="w-4 h-4 text-danger-600 mr-1" />}
              <span
                className={cn(
                  'text-sm font-medium',
                  isPositive && 'text-success-600',
                  isNegative && 'text-danger-600',
                  !isPositive && !isNegative && 'text-gray-600'
                )}
              >
                {change > 0 && '+'}{change.toFixed(1)}%
              </span>
              {changeLabel && (
                <span className="text-sm text-gray-500 ml-1">{changeLabel}</span>
              )}
            </div>
          )}
        </div>
        
        {icon && (
          <div className="p-3 bg-primary-50 rounded-lg">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}


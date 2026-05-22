import type { ReactNode } from 'react'
import { cn } from '../../lib/utils'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

/**
 * Empty state with optional CTA. Use whenever a list/grid has no data, so the
 * user gets feedback ("rien à afficher") AND a path forward, instead of a
 * silent blank area.
 */
export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center px-6 py-12',
        className,
      )}
      role="status"
    >
      {icon && (
        <div className="mb-4 p-3 bg-primary-50 rounded-full text-primary-600">{icon}</div>
      )}
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      {description && (
        <p className="mt-2 text-sm text-gray-600 max-w-md">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}

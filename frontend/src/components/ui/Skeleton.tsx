import { cn } from '../../lib/utils'

interface SkeletonProps {
  className?: string
  /** Pre-baked variant. Use these instead of raw width/height for consistency. */
  variant?: 'text' | 'title' | 'avatar' | 'card' | 'stat' | 'row'
}

/**
 * Animated placeholder. Use BEFORE the real content is available so layout
 * stays stable (no CLS) and the page never shows a blank flash.
 *
 * Example:
 *   {isLoading ? <Skeleton variant="stat" /> : <StatCard ... />}
 */
export function Skeleton({ className, variant }: SkeletonProps) {
  const variantClass: Record<NonNullable<SkeletonProps['variant']>, string> = {
    text: 'h-4 w-full',
    title: 'h-6 w-1/3',
    avatar: 'h-10 w-10 rounded-full',
    card: 'h-40 w-full',
    stat: 'h-32 w-full',
    row: 'h-12 w-full',
  }
  return (
    <div
      className={cn(
        'animate-pulse bg-gray-200 rounded-md',
        variant && variantClass[variant],
        className,
      )}
      aria-hidden="true"
    />
  )
}


/** Convenience: skeleton grid for the 4 KPI stat cards on the dashboard. */
export function StatGridSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: count }, (_, i) => (
        <Skeleton key={i} variant="stat" />
      ))}
    </div>
  )
}


/** Convenience: skeleton table rows. */
export function TableRowsSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-2">
      {Array.from({ length: rows }, (_, i) => (
        <Skeleton key={i} variant="row" />
      ))}
    </div>
  )
}

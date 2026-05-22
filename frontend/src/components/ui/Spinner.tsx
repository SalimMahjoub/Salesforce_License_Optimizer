import { Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

interface SpinnerProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
  /** Accessible label for screen readers. */
  label?: string
}

const SIZE: Record<NonNullable<SpinnerProps['size']>, string> = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-10 h-10',
}

export function Spinner({ className, size = 'md', label = 'Chargement' }: SpinnerProps) {
  return (
    <Loader2
      className={cn('animate-spin text-primary-600', SIZE[size], className)}
      role="status"
      aria-label={label}
    />
  )
}

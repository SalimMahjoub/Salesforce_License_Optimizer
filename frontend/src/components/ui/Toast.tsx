import { create } from 'zustand'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'
import { useEffect } from 'react'
import { cn } from '../../lib/utils'

type ToastKind = 'success' | 'error' | 'info'

interface ToastItem {
  id: string
  kind: ToastKind
  title: string
  description?: string
}

interface ToastState {
  toasts: ToastItem[]
  push: (t: Omit<ToastItem, 'id'>) => string
  dismiss: (id: string) => void
}

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  push: (t) => {
    const id = Math.random().toString(36).slice(2, 9)
    set({ toasts: [...get().toasts, { ...t, id }] })
    return id
  },
  dismiss: (id) =>
    set({ toasts: get().toasts.filter((x) => x.id !== id) }),
}))

/** Convenience: side-effect-free helpers (use from anywhere — hooks, mutations, …). */
export const toast = {
  success: (title: string, description?: string) =>
    useToastStore.getState().push({ kind: 'success', title, description }),
  error: (title: string, description?: string) =>
    useToastStore.getState().push({ kind: 'error', title, description }),
  info: (title: string, description?: string) =>
    useToastStore.getState().push({ kind: 'info', title, description }),
}

const KIND_STYLE: Record<ToastKind, { bg: string; ring: string; Icon: typeof CheckCircle2 }> = {
  success: { bg: 'bg-success-50', ring: 'ring-success-500', Icon: CheckCircle2 },
  error: { bg: 'bg-danger-50', ring: 'ring-danger-500', Icon: AlertCircle },
  info: { bg: 'bg-primary-50', ring: 'ring-primary-500', Icon: Info },
}

function ToastCard({ toast: t }: { toast: ToastItem }) {
  const dismiss = useToastStore((s) => s.dismiss)
  const { bg, ring, Icon } = KIND_STYLE[t.kind]

  useEffect(() => {
    const timer = setTimeout(() => dismiss(t.id), 4000)
    return () => clearTimeout(timer)
  }, [t.id, dismiss])

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        'flex items-start gap-3 p-3 rounded-lg shadow-md ring-1',
        bg,
        ring,
        'animate-in slide-in-from-right-5 duration-200',
      )}
    >
      <Icon className="w-5 h-5 mt-0.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-gray-900">{t.title}</div>
        {t.description && (
          <div className="text-sm text-gray-600 mt-0.5">{t.description}</div>
        )}
      </div>
      <button
        type="button"
        aria-label="Fermer la notification"
        className="text-gray-500 hover:text-gray-700"
        onClick={() => dismiss(t.id)}
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

/** Mount once at app root — renders the stack of active toasts. */
export function ToastViewport() {
  const toasts = useToastStore((s) => s.toasts)
  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      className="fixed top-4 right-4 z-50 w-80 max-w-[calc(100vw-2rem)] space-y-2"
    >
      {toasts.map((t) => (
        <ToastCard key={t.id} toast={t} />
      ))}
    </div>
  )
}

import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

interface Props {
  children: ReactNode
  fallback?: (error: Error, reset: () => void) => ReactNode
}

interface State {
  error: Error | null
}

/**
 * Catches render-time errors and shows a recoverable fallback. Use at the
 * route level so a bug in one page doesn't take the whole app down.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // In production, forward to Sentry. Keep the console log for dev.
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught:', error, info.componentStack)
  }

  reset = () => this.setState({ error: null })

  render() {
    if (this.state.error) {
      if (this.props.fallback) return this.props.fallback(this.state.error, this.reset)
      return (
        <div className="min-h-[400px] flex items-center justify-center p-6">
          <div className="max-w-md text-center">
            <div className="mx-auto mb-4 p-3 bg-danger-50 rounded-full text-danger-600 inline-block">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h2 className="text-xl font-semibold text-gray-900">
              Une erreur est survenue
            </h2>
            <p className="text-sm text-gray-600 mt-2">
              {this.state.error.message || 'Erreur inattendue dans cette page.'}
            </p>
            <button
              type="button"
              className="btn btn-primary mt-6"
              onClick={this.reset}
            >
              Réessayer
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

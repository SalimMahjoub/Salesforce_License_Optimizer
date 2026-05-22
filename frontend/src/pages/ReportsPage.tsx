import { Download, FileText } from 'lucide-react'
import { Card } from '../components/ui/Card'
import { Skeleton } from '../components/ui/Skeleton'
import { toast } from '../components/ui/Toast'
import { useCfoPlan } from '../hooks/useAnalysis'
import { formatCurrency } from '../lib/utils'
import { useAppStore } from '../stores/appStore'

export function ReportsPage() {
  const orgId = useAppStore((s) => s.currentOrg)
  const { data: plan, isLoading, isError, error } = useCfoPlan(orgId)

  const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const pdfUrl = `${apiBase}/api/v1/reports/${orgId}/pdf`

  return (
    <div className="space-y-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Rapport CFO</h1>
          <p className="text-gray-600 mt-1">
            Plan d'action généré par IA — prêt à présenter à la direction financière.
          </p>
        </div>
        <a
          href={pdfUrl}
          className="btn btn-primary inline-flex items-center gap-2"
          target="_blank"
          rel="noopener noreferrer"
          onClick={() => toast.info('Génération du PDF…', 'Le téléchargement va démarrer.')}
        >
          <Download className="w-4 h-4" />
          Télécharger PDF
        </a>
      </header>

      {isError && (
        <Card>
          <div className="p-4 text-sm text-danger-700 bg-danger-50 rounded">
            Erreur : {(error as Error).message}
          </div>
        </Card>
      )}

      {isLoading && (
        <Card>
          <div className="space-y-4" aria-live="polite">
            <Skeleton variant="title" />
            <Skeleton variant="text" className="w-2/3" />
            <Skeleton variant="text" />
            <Skeleton variant="text" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-16 w-full" />
          </div>
        </Card>
      )}

      {plan && (
        <>
          <Card>
            <div className="flex items-start gap-4">
              <FileText className="w-8 h-8 text-primary-600 flex-shrink-0 mt-1" />
              <div>
                <h2 className="text-xl font-semibold text-gray-900">{plan.title}</h2>
                <p className="text-gray-700 mt-2">{plan.executive_summary}</p>
                <div className="flex flex-wrap gap-4 mt-4 text-sm">
                  <span className="text-gray-600">
                    Économies mensuelles :{' '}
                    <strong className="text-success-700">
                      {formatCurrency(plan.total_estimated_savings)}
                    </strong>
                  </span>
                  <span className="text-gray-600">
                    Économies annuelles :{' '}
                    <strong className="text-success-700">
                      {formatCurrency(plan.annual_estimated_savings)}
                    </strong>
                  </span>
                  <span className="text-gray-600">
                    Calendrier : <strong>{plan.timeline}</strong>
                  </span>
                  {plan.model_version && (
                    <span className="text-gray-500">
                      Modèle : <code>{plan.model_version}</code>
                    </span>
                  )}
                </div>
              </div>
            </div>
          </Card>

          <Card title="Étapes du plan">
            <ol className="space-y-4">
              {plan.steps.map((step, i) => (
                <li key={i} className="border-l-4 border-primary-500 pl-4">
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-gray-900">
                      {i + 1}. {step.title}
                    </h3>
                    <span className="text-sm text-gray-500 whitespace-nowrap ml-4">
                      {step.duration_days} jours
                    </span>
                  </div>
                  <p className="text-gray-700 mt-1">{step.description}</p>
                  {step.resources.length > 0 && (
                    <p className="text-sm text-gray-600 mt-2">
                      <strong>Ressources :</strong> {step.resources.join(', ')}
                    </p>
                  )}
                  {step.success_criteria.length > 0 && (
                    <ul className="text-sm text-gray-600 mt-1 list-disc list-inside">
                      {step.success_criteria.map((c, j) => (
                        <li key={j}>{c}</li>
                      ))}
                    </ul>
                  )}
                </li>
              ))}
            </ol>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Quick wins">
              <ul className="space-y-2">
                {plan.quick_wins.map((w, i) => (
                  <li key={i} className="text-sm text-gray-700 flex gap-2">
                    <span className="text-success-600">✓</span> {w}
                  </li>
                ))}
              </ul>
            </Card>
            <Card title="Risques &amp; mitigation">
              <ul className="space-y-3">
                {plan.risks.map((r, i) => (
                  <li key={i} className="text-sm">
                    <div className="font-medium text-gray-900">{r.risk}</div>
                    <div className="text-gray-600 mt-1">→ {r.mitigation}</div>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </>
      )}
    </div>
  )
}

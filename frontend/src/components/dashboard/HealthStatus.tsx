import { CheckCircle, XCircle, AlertCircle, Server } from 'lucide-react'
import type { HealthResponse } from '../../api/types'
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card'

interface HealthStatusProps {
  health: HealthResponse
}

export default function HealthStatus({ health }: HealthStatusProps) {
  const services = [
    {
      name: 'Claude (LLM)',
      status: health.claude_status,
      description: 'Génération de réponses',
    },
    {
      name: 'Voyage AI',
      status: health.voyage_status,
      description: 'Embeddings vectoriels',
    },
    {
      name: 'ChromaDB',
      status: health.chroma_status,
      description: 'Base de données vectorielle',
    },
  ]

  const getStatusIcon = (status: string) => {
    if (status === 'ok' || status === 'healthy') {
      return <CheckCircle className="h-5 w-5 text-green-500" />
    }
    if (status === 'error' || status === 'unavailable') {
      return <XCircle className="h-5 w-5 text-red-500" />
    }
    return <AlertCircle className="h-5 w-5 text-yellow-500" />
  }

  const getStatusText = (status: string) => {
    if (status === 'ok' || status === 'healthy') return 'Opérationnel'
    if (status === 'error' || status === 'unavailable') return 'Indisponible'
    return 'Dégradé'
  }

  const getStatusColor = (status: string) => {
    if (status === 'ok' || status === 'healthy') return 'text-green-600 dark:text-green-400'
    if (status === 'error' || status === 'unavailable') return 'text-red-600 dark:text-red-400'
    return 'text-yellow-600 dark:text-yellow-400'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <div className="flex items-center gap-2">
            <Server className="h-5 w-5 text-gray-400" />
            État des Services
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {services.map((service) => (
            <div
              key={service.name}
              className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50"
            >
              <div>
                <p className="font-medium text-gray-900 dark:text-gray-100">
                  {service.name}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {service.description}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {getStatusIcon(service.status)}
                <span className={`text-sm font-medium ${getStatusColor(service.status)}`}>
                  {getStatusText(service.status)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

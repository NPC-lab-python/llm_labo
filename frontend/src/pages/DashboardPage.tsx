import { useHealth } from '../hooks/useHealth'
import { useStats } from '../hooks/useStats'
import {
  StatsOverview,
  HealthStatus,
  QualityChart,
  LowQualityList,
  MissingFieldsChart,
} from '../components/dashboard'
import { LoadingOverlay } from '../components/ui/Spinner'
import Badge from '../components/ui/Badge'

export default function DashboardPage() {
  const { data: health, isLoading: healthLoading, error: healthError } = useHealth()
  const { data: stats, isLoading: statsLoading, error: statsError } = useStats()

  const isLoading = healthLoading || statsLoading
  const hasError = healthError || statsError

  if (isLoading) {
    return (
      <div className="p-6">
        <LoadingOverlay message="Chargement des statistiques..." />
      </div>
    )
  }

  if (hasError) {
    return (
      <div className="p-6">
        <div className="text-center py-12">
          <Badge variant="error">Erreur de chargement des statistiques</Badge>
          <p className="text-gray-500 dark:text-gray-400 mt-2">
            Vérifiez que l'API est accessible
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Vue d'ensemble du système RAG
        </p>
      </div>

      {/* Stats Overview */}
      {stats && <StatsOverview stats={stats} />}

      {/* Grille principale */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Colonne gauche */}
        <div className="space-y-6">
          {health && <HealthStatus health={health} />}
          {stats && <QualityChart stats={stats} />}
        </div>

        {/* Colonne droite */}
        <div className="space-y-6">
          {stats && <MissingFieldsChart stats={stats} />}
          {stats && <LowQualityList stats={stats} />}
        </div>
      </div>
    </div>
  )
}

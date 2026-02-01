import { FileText, Star, AlertTriangle, TrendingUp } from 'lucide-react'
import type { MetadataQualityStats } from '../../api/types'
import Card from '../ui/Card'

interface StatsOverviewProps {
  stats: MetadataQualityStats
}

export default function StatsOverview({ stats }: StatsOverviewProps) {
  const statItems = [
    {
      label: 'Total Documents',
      value: stats.total_documents,
      icon: FileText,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-100 dark:bg-blue-900/30',
    },
    {
      label: 'Score Moyen',
      value: `${(stats.average_score * 100).toFixed(0)}%`,
      icon: Star,
      color: 'text-yellow-600 dark:text-yellow-400',
      bgColor: 'bg-yellow-100 dark:bg-yellow-900/30',
    },
    {
      label: 'Qualité Faible',
      value: stats.low_quality_count,
      icon: AlertTriangle,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-100 dark:bg-red-900/30',
    },
    {
      label: 'Excellents',
      value: stats.score_distribution['excellent'] || stats.score_distribution['Excellent'] || 0,
      icon: TrendingUp,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-100 dark:bg-green-900/30',
    },
  ]

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {statItems.map((item) => (
        <Card key={item.label} className="flex items-center gap-4">
          <div className={`p-3 rounded-xl ${item.bgColor}`}>
            <item.icon className={`h-6 w-6 ${item.color}`} />
          </div>
          <div>
            <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              {item.value}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">{item.label}</p>
          </div>
        </Card>
      ))}
    </div>
  )
}

import { AlertTriangle, ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { MetadataQualityStats } from '../../api/types'
import Card, { CardHeader, CardTitle, CardContent } from '../ui/Card'
import Badge from '../ui/Badge'
import Button from '../ui/Button'

interface LowQualityListProps {
  stats: MetadataQualityStats
}

export default function LowQualityList({ stats }: LowQualityListProps) {
  const documents = stats.documents_needing_review || []

  if (documents.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Documents à Améliorer
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p>Tous les documents ont des métadonnées de qualité suffisante.</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between w-full">
          <CardTitle>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Documents à Améliorer
            </div>
          </CardTitle>
          <Link to="/documents">
            <Button variant="ghost" size="sm" rightIcon={<ExternalLink className="h-4 w-4" />}>
              Voir tous
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {documents.slice(0, 5).map((doc) => (
            <div
              key={doc.id}
              className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50"
            >
              <div className="min-w-0 flex-1">
                <p className="font-medium text-gray-900 dark:text-gray-100 truncate">
                  {doc.title}
                </p>
              </div>
              <Badge
                variant={doc.score < 0.3 ? 'error' : doc.score < 0.5 ? 'warning' : 'default'}
                size="sm"
              >
                {Math.round(doc.score * 100)}%
              </Badge>
            </div>
          ))}
        </div>
        {documents.length > 5 && (
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-3 text-center">
            +{documents.length - 5} autres documents
          </p>
        )}
      </CardContent>
    </Card>
  )
}

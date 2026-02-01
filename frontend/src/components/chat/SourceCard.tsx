import { FileText, Calendar, Users, ExternalLink } from 'lucide-react'
import type { Source } from '../../api/types'
import { getDocumentPdfUrl } from '../../api/endpoints'
import Badge from '../ui/Badge'

interface SourceCardProps {
  source: Source
  index: number
}

export default function SourceCard({ source, index }: SourceCardProps) {
  const relevancePercent = Math.round(source.relevance_score * 100)

  const getRelevanceVariant = (score: number) => {
    if (score >= 80) return 'success'
    if (score >= 60) return 'info'
    if (score >= 40) return 'warning'
    return 'default'
  }

  const pdfUrl = getDocumentPdfUrl(source.document_id, source.page ?? undefined)

  const handleClick = () => {
    window.open(pdfUrl, '_blank')
  }

  return (
    <button
      onClick={handleClick}
      className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 hover:border-primary-400 dark:hover:border-primary-600 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer group"
    >
      <div className="flex items-start gap-3">
        <div className="shrink-0 w-6 h-6 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 flex items-center justify-center text-xs font-bold">
          {index + 1}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-2">
            <h4 className="font-medium text-gray-900 dark:text-gray-100 text-sm line-clamp-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
              {source.title}
            </h4>
            <ExternalLink className="h-4 w-4 shrink-0 text-gray-400 group-hover:text-primary-500 transition-colors" />
          </div>
          <div className="flex flex-wrap items-center gap-2 mt-1.5 text-xs text-gray-500 dark:text-gray-400">
            {source.authors && (
              <span className="flex items-center gap-1">
                <Users className="h-3 w-3" />
                <span className="truncate max-w-[150px]">{source.authors}</span>
              </span>
            )}
            {source.year && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {source.year}
              </span>
            )}
            {source.page && (
              <span className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                p.{source.page}
              </span>
            )}
          </div>
        </div>
        <Badge size="sm" variant={getRelevanceVariant(relevancePercent)}>
          {relevancePercent}%
        </Badge>
      </div>
    </button>
  )
}

interface SourceListProps {
  sources: Source[]
}

export function SourceList({ sources }: SourceListProps) {
  if (!sources.length) return null

  return (
    <div className="mt-4">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
        Sources ({sources.length})
      </h3>
      <div className="space-y-2">
        {sources.map((source, index) => (
          <SourceCard key={`${source.document_id}-${index}`} source={source} index={index} />
        ))}
      </div>
    </div>
  )
}

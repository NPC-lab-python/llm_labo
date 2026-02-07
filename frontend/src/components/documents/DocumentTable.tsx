import { FileText, Calendar, Users, Trash2, Layers, ScrollText } from 'lucide-react'
import type { DocumentInfo } from '../../api/types'
import Badge from '../ui/Badge'
import Button from '../ui/Button'

interface DocumentTableProps {
  documents: DocumentInfo[]
  onDelete: (id: string) => void
  onSummary: (doc: DocumentInfo) => void
  isDeleting?: string
  isSummarizing?: string
}

export default function DocumentTable({ documents, onDelete, onSummary, isDeleting, isSummarizing }: DocumentTableProps) {
  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'indexed':
        return 'success'
      case 'pending':
        return 'warning'
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'indexed':
        return 'Indexé'
      case 'pending':
        return 'En attente'
      case 'error':
        return 'Erreur'
      default:
        return status
    }
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
        <p>Aucun document trouvé</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Document
            </th>
            <th className="text-left py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Auteurs
            </th>
            <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Année
            </th>
            <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Chunks
            </th>
            <th className="text-center py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Statut
            </th>
            <th className="text-right py-3 px-4 text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {documents.map((doc) => (
            <tr
              key={doc.id}
              className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
            >
              <td className="py-3 px-4">
                <div className="flex items-center gap-3">
                  <FileText className="h-5 w-5 text-gray-400 shrink-0" />
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 dark:text-gray-100 truncate max-w-xs">
                      {doc.title}
                    </p>
                    {doc.page_count && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {doc.page_count} pages
                      </p>
                    )}
                  </div>
                </div>
              </td>
              <td className="py-3 px-4">
                {doc.authors ? (
                  <div className="flex items-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                    <Users className="h-4 w-4 shrink-0" />
                    <span className="truncate max-w-[150px]">{doc.authors}</span>
                  </div>
                ) : (
                  <span className="text-gray-400 dark:text-gray-500">-</span>
                )}
              </td>
              <td className="py-3 px-4 text-center">
                {doc.year ? (
                  <div className="flex items-center justify-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                    <Calendar className="h-4 w-4" />
                    {doc.year}
                  </div>
                ) : (
                  <span className="text-gray-400 dark:text-gray-500">-</span>
                )}
              </td>
              <td className="py-3 px-4 text-center">
                <div className="flex items-center justify-center gap-1 text-sm text-gray-600 dark:text-gray-400">
                  <Layers className="h-4 w-4" />
                  {doc.chunk_count}
                </div>
              </td>
              <td className="py-3 px-4 text-center">
                <Badge variant={getStatusVariant(doc.status)} size="sm">
                  {getStatusLabel(doc.status)}
                </Badge>
              </td>
              <td className="py-3 px-4">
                <div className="flex items-center justify-end gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onSummary(doc)}
                    isLoading={isSummarizing === doc.id}
                    disabled={doc.status !== 'indexed'}
                    className="text-primary-600 hover:text-primary-700 hover:bg-primary-50 dark:text-primary-400 dark:hover:bg-primary-900/20"
                    title="Générer un résumé"
                  >
                    <ScrollText className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDelete(doc.id)}
                    isLoading={isDeleting === doc.id}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                    title="Supprimer"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

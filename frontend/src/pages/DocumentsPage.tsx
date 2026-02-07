import { useState } from 'react'
import { Search, Upload, ChevronLeft, ChevronRight } from 'lucide-react'
import { useDocuments, useDeleteDocument, useGenerateSummary } from '../hooks/useDocuments'
import { DocumentTable, UploadModal, DeleteConfirmModal, SummaryModal } from '../components/documents'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Badge from '../components/ui/Badge'
import { LoadingOverlay } from '../components/ui/Spinner'
import type { DocumentInfo } from '../api/types'

const LIMIT = 10

export default function DocumentsPage() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [uploadModalOpen, setUploadModalOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<DocumentInfo | null>(null)
  const [summaryTarget, setSummaryTarget] = useState<DocumentInfo | null>(null)
  const [summaryContent, setSummaryContent] = useState<string | null>(null)
  const [summaryError, setSummaryError] = useState<string | null>(null)

  const { data, isLoading, error } = useDocuments({
    page,
    limit: LIMIT,
    search: search || undefined,
    status: statusFilter || undefined,
  })

  const deleteMutation = useDeleteDocument()
  const summaryMutation = useGenerateSummary()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteMutation.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
  }

  const handleSummary = async (doc: DocumentInfo) => {
    setSummaryTarget(doc)
    setSummaryContent(null)
    setSummaryError(null)

    try {
      const result = await summaryMutation.mutateAsync(doc.id)
      setSummaryContent(result.summary)
    } catch {
      setSummaryError('Erreur lors de la génération du résumé')
    }
  }

  const closeSummaryModal = () => {
    setSummaryTarget(null)
    setSummaryContent(null)
    setSummaryError(null)
  }

  const totalPages = data ? Math.ceil(data.total / LIMIT) : 0

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Documents
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Gérez vos articles de recherche
          </p>
        </div>
        <Button
          onClick={() => setUploadModalOpen(true)}
          leftIcon={<Upload className="h-4 w-4" />}
        >
          Uploader
        </Button>
      </div>

      {/* Filtres */}
      <Card padding="md">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <Input
              placeholder="Rechercher par titre..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
            />
          </div>
          <div className="flex gap-2">
            {['', 'indexed', 'pending', 'error'].map((status) => (
              <button
                key={status || 'all'}
                type="button"
                onClick={() => {
                  setStatusFilter(status)
                  setPage(1)
                }}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  statusFilter === status
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                    : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                {status === '' && 'Tous'}
                {status === 'indexed' && 'Indexés'}
                {status === 'pending' && 'En attente'}
                {status === 'error' && 'Erreurs'}
              </button>
            ))}
          </div>
        </form>
      </Card>

      {/* Table */}
      <Card padding="none">
        {isLoading ? (
          <LoadingOverlay message="Chargement des documents..." />
        ) : error ? (
          <div className="p-6 text-center">
            <Badge variant="error">Erreur de chargement</Badge>
          </div>
        ) : data ? (
          <>
            <DocumentTable
              documents={data.documents}
              onDelete={(id) => {
                const doc = data.documents.find((d) => d.id === id)
                if (doc) setDeleteTarget(doc)
              }}
              onSummary={handleSummary}
              isDeleting={deleteMutation.isPending ? deleteMutation.variables : undefined}
              isSummarizing={summaryMutation.isPending ? summaryTarget?.id : undefined}
            />

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 dark:border-gray-700">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {data.total} document{data.total > 1 ? 's' : ''} au total
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="text-sm text-gray-600 dark:text-gray-400 px-2">
                    {page} / {totalPages}
                  </span>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}
          </>
        ) : null}
      </Card>

      {/* Modals */}
      <UploadModal isOpen={uploadModalOpen} onClose={() => setUploadModalOpen(false)} />
      <DeleteConfirmModal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title={deleteTarget?.title || ''}
        isLoading={deleteMutation.isPending}
      />
      <SummaryModal
        isOpen={!!summaryTarget}
        onClose={closeSummaryModal}
        title={summaryTarget?.title || ''}
        summary={summaryContent}
        isLoading={summaryMutation.isPending}
        error={summaryError}
      />
    </div>
  )
}

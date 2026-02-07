import { useState } from 'react'
import { FolderOpen, RefreshCw, CheckCircle, AlertCircle, Loader2, Trash2, AlertTriangle } from 'lucide-react'
import { useIndexBatch, useReindexEmbeddings, useResetDatabases } from '../hooks/useIndexation'
import Card, { CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Badge from '../components/ui/Badge'
import Modal, { ModalFooter } from '../components/ui/Modal'

export default function IndexationPage() {
  const [folderPath, setFolderPath] = useState('')
  const [batchResult, setBatchResult] = useState<{
    processed: number
    errors: string[]
  } | null>(null)
  const [reindexResult, setReindexResult] = useState<{
    reindexed: number
    total: number
    errors: string[]
    message: string
  } | null>(null)
  const [resetResult, setResetResult] = useState<{
    documents_deleted: number
    chunks_deleted: number
    message: string
  } | null>(null)
  const [showResetModal, setShowResetModal] = useState(false)

  const indexBatchMutation = useIndexBatch()
  const reindexMutation = useReindexEmbeddings()
  const resetMutation = useResetDatabases()

  const handleIndexBatch = async () => {
    if (!folderPath.trim()) return

    setBatchResult(null)
    try {
      const result = await indexBatchMutation.mutateAsync({ folder_path: folderPath })
      setBatchResult({
        processed: result.processed,
        errors: result.errors,
      })
    } catch {
      setBatchResult({
        processed: 0,
        errors: ['Erreur lors de l\'indexation'],
      })
    }
  }

  const handleReindex = async () => {
    setReindexResult(null)
    try {
      const result = await reindexMutation.mutateAsync(undefined)
      setReindexResult(result)
    } catch {
      setReindexResult({
        reindexed: 0,
        total: 0,
        errors: ['Erreur lors de la réindexation'],
        message: 'Échec de la réindexation',
      })
    }
  }

  const handleReset = async () => {
    setResetResult(null)
    try {
      const result = await resetMutation.mutateAsync()
      setResetResult(result)
      setShowResetModal(false)
    } catch {
      setResetResult({
        documents_deleted: 0,
        chunks_deleted: 0,
        message: 'Échec de la réinitialisation',
      })
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Indexation
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Indexer des documents et gérer les bases de données
        </p>
      </div>

      {/* Réinitialisation */}
      <Card className="border-red-200 dark:border-red-900">
        <CardHeader>
          <CardTitle>
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <Trash2 className="h-5 w-5" />
              Réinitialisation complète
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Supprime tous les documents et embeddings des bases de données (SQLite + ChromaDB).
            Utilisez cette option avant de réindexer avec GROBID pour repartir de zéro.
          </p>

          <div className="space-y-4">
            <div className="p-4 rounded-lg border border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-900/20">
              <p className="text-sm text-red-800 dark:text-red-200">
                <strong>Attention :</strong> Cette action est irréversible. Tous les documents
                indexés seront supprimés. Vous devrez réindexer vos PDFs après cette opération.
              </p>
            </div>

            <Button
              onClick={() => setShowResetModal(true)}
              variant="danger"
              leftIcon={<Trash2 className="h-4 w-4" />}
            >
              Réinitialiser les bases de données
            </Button>

            {resetResult && (
              <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50 space-y-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    {resetResult.message}
                  </span>
                </div>
                <div className="flex gap-2">
                  <Badge variant="default">{resetResult.documents_deleted} documents supprimés</Badge>
                  <Badge variant="default">{resetResult.chunks_deleted} chunks supprimés</Badge>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Indexation batch */}
        <Card>
          <CardHeader>
            <CardTitle>
              <div className="flex items-center gap-2">
                <FolderOpen className="h-5 w-5 text-primary-600" />
                Indexation par dossier
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Indexe tous les fichiers PDF d'un dossier. Si GROBID est disponible (port 8070),
              les métadonnées seront extraites avec une meilleure précision.
            </p>

            <div className="space-y-4">
              <Input
                label="Chemin du dossier"
                placeholder="C:\Users\...\pdfs ou ./data/pdfs"
                value={folderPath}
                onChange={(e) => setFolderPath(e.target.value)}
              />

              <Button
                onClick={handleIndexBatch}
                isLoading={indexBatchMutation.isPending}
                disabled={!folderPath.trim()}
                leftIcon={<FolderOpen className="h-4 w-4" />}
                className="w-full"
              >
                Indexer le dossier
              </Button>

              {indexBatchMutation.isPending && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Indexation en cours... Cela peut prendre plusieurs minutes.
                </div>
              )}

              {batchResult && (
                <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50 space-y-2">
                  <div className="flex items-center gap-2">
                    {batchResult.errors.length === 0 ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-yellow-500" />
                    )}
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {batchResult.processed} document(s) indexé(s)
                    </span>
                  </div>

                  {batchResult.errors.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium text-red-600 dark:text-red-400 mb-1">
                        Erreurs ({batchResult.errors.length}):
                      </p>
                      <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 max-h-32 overflow-y-auto">
                        {batchResult.errors.map((error, i) => (
                          <li key={i} className="truncate">• {error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Réindexation embeddings */}
        <Card>
          <CardHeader>
            <CardTitle>
              <div className="flex items-center gap-2">
                <RefreshCw className="h-5 w-5 text-primary-600" />
                Mise à jour des embeddings
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Régénère les embeddings de tous les documents indexés. Utile après un changement
              de modèle d'embedding ou pour améliorer la qualité de recherche.
            </p>

            <div className="space-y-4">
              <div className="p-4 rounded-lg border border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-900/20">
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  <strong>Attention :</strong> Cette opération peut prendre plusieurs minutes
                  selon le nombre de documents et consommera des crédits API Voyage AI.
                </p>
              </div>

              <Button
                onClick={handleReindex}
                isLoading={reindexMutation.isPending}
                variant="secondary"
                leftIcon={<RefreshCw className="h-4 w-4" />}
                className="w-full"
              >
                Réindexer tous les embeddings
              </Button>

              {reindexMutation.isPending && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Réindexation en cours... Cela peut prendre plusieurs minutes.
                </div>
              )}

              {reindexResult && (
                <div className="p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50 space-y-2">
                  <div className="flex items-center gap-2">
                    {reindexResult.errors.length === 0 ? (
                      <CheckCircle className="h-5 w-5 text-green-500" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-yellow-500" />
                    )}
                    <span className="font-medium text-gray-900 dark:text-gray-100">
                      {reindexResult.message}
                    </span>
                  </div>

                  <div className="flex gap-2">
                    <Badge variant="success">{reindexResult.reindexed} réindexés</Badge>
                    <Badge variant="default">{reindexResult.total} total</Badge>
                    {reindexResult.errors.length > 0 && (
                      <Badge variant="error">{reindexResult.errors.length} erreurs</Badge>
                    )}
                  </div>

                  {reindexResult.errors.length > 0 && (
                    <div className="mt-2">
                      <p className="text-sm font-medium text-red-600 dark:text-red-400 mb-1">
                        Erreurs:
                      </p>
                      <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 max-h-32 overflow-y-auto">
                        {reindexResult.errors.map((error, i) => (
                          <li key={i} className="truncate">• {error}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Instructions */}
      <Card>
        <CardHeader>
          <CardTitle>Instructions - Réindexation avec GROBID</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <h4 className="text-gray-900 dark:text-gray-100">1. Lancer GROBID (optionnel mais recommandé)</h4>
            <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded-lg text-sm overflow-x-auto">
              docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0
            </pre>
            <p className="text-gray-600 dark:text-gray-400">
              GROBID améliore l'extraction des métadonnées (titre, auteurs, abstract, DOI, références...).
            </p>

            <h4 className="text-gray-900 dark:text-gray-100 mt-4">2. Réinitialiser les bases de données</h4>
            <p className="text-gray-600 dark:text-gray-400">
              Cliquez sur "Réinitialiser les bases de données" pour supprimer tous les documents existants.
            </p>

            <h4 className="text-gray-900 dark:text-gray-100 mt-4">3. Réindexer les PDFs</h4>
            <p className="text-gray-600 dark:text-gray-400">
              Entrez le chemin vers votre dossier de PDFs (ex: <code>./data/pdfs</code>) et cliquez sur "Indexer le dossier".
              Si GROBID est actif, il sera utilisé automatiquement pour l'extraction des métadonnées.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Modal de confirmation reset */}
      <Modal
        isOpen={showResetModal}
        onClose={() => setShowResetModal(false)}
        title="Confirmer la réinitialisation"
        size="sm"
      >
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
            <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
          </div>
          <p className="text-gray-600 dark:text-gray-400 mb-2">
            Êtes-vous sûr de vouloir réinitialiser les bases de données ?
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Tous les documents et embeddings seront supprimés définitivement.
          </p>
        </div>

        <ModalFooter>
          <Button variant="secondary" onClick={() => setShowResetModal(false)} disabled={resetMutation.isPending}>
            Annuler
          </Button>
          <Button variant="danger" onClick={handleReset} isLoading={resetMutation.isPending}>
            Réinitialiser
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  )
}

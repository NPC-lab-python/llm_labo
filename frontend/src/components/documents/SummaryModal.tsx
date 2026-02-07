import { useState } from 'react'
import { FileText, Loader2, Copy, Download, Check } from 'lucide-react'
import Modal from '../ui/Modal'
import Button from '../ui/Button'

interface SummaryModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  summary: string | null
  isLoading: boolean
  error: string | null
}

export default function SummaryModal({
  isOpen,
  onClose,
  title,
  summary,
  isLoading,
  error,
}: SummaryModalProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (!summary) return
    try {
      await navigator.clipboard.writeText(summary)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Erreur copie:', err)
    }
  }

  const handleDownload = (format: 'txt' | 'md') => {
    if (!summary) return

    const sanitizedTitle = title.replace(/[^a-zA-Z0-9àâäéèêëïîôùûüç\s-]/g, '').substring(0, 50)
    const filename = `resume_${sanitizedTitle}.${format}`

    let content = summary
    if (format === 'md') {
      content = `# Résumé : ${title}\n\n${summary}`
    }

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Résumé du document" size="lg">
      <div className="space-y-4">
        {/* Titre du document */}
        <div className="flex items-start gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
          <FileText className="h-5 w-5 text-primary-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm text-gray-500 dark:text-gray-400">Document</p>
            <p className="font-medium text-gray-900 dark:text-gray-100">{title}</p>
          </div>
        </div>

        {/* Contenu */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Génération du résumé en cours...
            </p>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {summary && !isLoading && (
          <div className="prose prose-sm dark:prose-invert max-w-none max-h-[60vh] overflow-y-auto">
            <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
              {summary}
            </div>
          </div>
        )}

        {/* Footer avec actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          {/* Actions de sauvegarde */}
          {summary && !isLoading && (
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleCopy}
                leftIcon={copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              >
                {copied ? 'Copié !' : 'Copier'}
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleDownload('txt')}
                leftIcon={<Download className="h-4 w-4" />}
              >
                .txt
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleDownload('md')}
                leftIcon={<Download className="h-4 w-4" />}
              >
                .md
              </Button>
            </div>
          )}
          {(!summary || isLoading) && <div />}

          <Button variant="secondary" onClick={onClose}>
            Fermer
          </Button>
        </div>
      </div>
    </Modal>
  )
}

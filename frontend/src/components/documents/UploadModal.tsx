import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, CheckCircle, AlertCircle } from 'lucide-react'
import Modal, { ModalFooter } from '../ui/Modal'
import Button from '../ui/Button'
import { useUploadDocument } from '../../hooks/useDocuments'

interface UploadModalProps {
  isOpen: boolean
  onClose: () => void
}

interface FileStatus {
  file: File
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

export default function UploadModal({ isOpen, onClose }: UploadModalProps) {
  const [files, setFiles] = useState<FileStatus[]>([])
  const uploadMutation = useUploadDocument()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map((file) => ({
      file,
      status: 'pending' as const,
    }))
    setFiles((prev) => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    multiple: true,
  })

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const uploadFiles = async () => {
    for (let i = 0; i < files.length; i++) {
      if (files[i].status !== 'pending') continue

      setFiles((prev) =>
        prev.map((f, idx) => (idx === i ? { ...f, status: 'uploading' } : f))
      )

      try {
        await uploadMutation.mutateAsync(files[i].file)
        setFiles((prev) =>
          prev.map((f, idx) => (idx === i ? { ...f, status: 'success' } : f))
        )
      } catch (error) {
        setFiles((prev) =>
          prev.map((f, idx) =>
            idx === i
              ? { ...f, status: 'error', error: 'Erreur lors de l\'upload' }
              : f
          )
        )
      }
    }
  }

  const handleClose = () => {
    setFiles([])
    onClose()
  }

  const pendingCount = files.filter((f) => f.status === 'pending').length
  const isUploading = files.some((f) => f.status === 'uploading')

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Uploader des PDFs" size="lg">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 dark:hover:border-primary-500'
        }`}
      >
        <input {...getInputProps()} />
        <Upload className="h-10 w-10 mx-auto mb-3 text-gray-400" />
        {isDragActive ? (
          <p className="text-primary-600 dark:text-primary-400">
            Déposez les fichiers ici...
          </p>
        ) : (
          <>
            <p className="text-gray-600 dark:text-gray-400 mb-1">
              Glissez-déposez des fichiers PDF ici
            </p>
            <p className="text-sm text-gray-400 dark:text-gray-500">
              ou cliquez pour sélectionner
            </p>
          </>
        )}
      </div>

      {/* Liste des fichiers */}
      {files.length > 0 && (
        <div className="mt-4 space-y-2 max-h-60 overflow-y-auto">
          {files.map((item, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-800"
            >
              <File className="h-5 w-5 text-gray-400 shrink-0" />
              <span className="flex-1 text-sm text-gray-700 dark:text-gray-300 truncate">
                {item.file.name}
              </span>
              <span className="text-xs text-gray-400">
                {(item.file.size / 1024 / 1024).toFixed(1)} MB
              </span>
              {item.status === 'pending' && (
                <button
                  onClick={() => removeFile(index)}
                  className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <X className="h-4 w-4" />
                </button>
              )}
              {item.status === 'uploading' && (
                <div className="h-4 w-4 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
              )}
              {item.status === 'success' && (
                <CheckCircle className="h-5 w-5 text-green-500" />
              )}
              {item.status === 'error' && (
                <span title={item.error}>
                  <AlertCircle className="h-5 w-5 text-red-500" />
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      <ModalFooter>
        <Button variant="secondary" onClick={handleClose}>
          Fermer
        </Button>
        <Button
          onClick={uploadFiles}
          disabled={pendingCount === 0}
          isLoading={isUploading}
        >
          Uploader {pendingCount > 0 && `(${pendingCount})`}
        </Button>
      </ModalFooter>
    </Modal>
  )
}

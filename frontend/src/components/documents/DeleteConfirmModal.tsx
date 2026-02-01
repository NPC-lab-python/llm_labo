import { AlertTriangle } from 'lucide-react'
import Modal, { ModalFooter } from '../ui/Modal'
import Button from '../ui/Button'

interface DeleteConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  isLoading?: boolean
}

export default function DeleteConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  isLoading,
}: DeleteConfirmModalProps) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Confirmer la suppression" size="sm">
      <div className="flex flex-col items-center text-center">
        <div className="w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
          <AlertTriangle className="h-6 w-6 text-red-600 dark:text-red-400" />
        </div>
        <p className="text-gray-600 dark:text-gray-400 mb-2">
          Êtes-vous sûr de vouloir supprimer ce document ?
        </p>
        <p className="font-medium text-gray-900 dark:text-gray-100 text-sm">
          "{title}"
        </p>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Cette action est irréversible.
        </p>
      </div>

      <ModalFooter>
        <Button variant="secondary" onClick={onClose} disabled={isLoading}>
          Annuler
        </Button>
        <Button variant="danger" onClick={onConfirm} isLoading={isLoading}>
          Supprimer
        </Button>
      </ModalFooter>
    </Modal>
  )
}

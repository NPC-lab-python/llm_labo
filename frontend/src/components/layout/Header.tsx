import { Moon, Sun, Activity } from 'lucide-react'
import { useHealth } from '../../hooks/useHealth'
import Badge from '../ui/Badge'

interface HeaderProps {
  darkMode: boolean
  toggleDarkMode: () => void
}

export default function Header({ darkMode, toggleDarkMode }: HeaderProps) {
  const { data: health, isLoading } = useHealth()

  const getStatusVariant = (status: string | undefined) => {
    if (!status || status === 'error') return 'error'
    if (status === 'ok' || status === 'healthy') return 'success'
    return 'warning'
  }

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
      {/* Statut services */}
      <div className="flex items-center gap-4">
        {isLoading ? (
          <span className="text-sm text-gray-400">Vérification des services...</span>
        ) : health ? (
          <div className="flex items-center gap-3">
            <Activity className="h-4 w-4 text-gray-400" />
            <div className="flex items-center gap-2">
              <Badge size="sm" variant={getStatusVariant(health.claude_status)}>
                Claude
              </Badge>
              <Badge size="sm" variant={getStatusVariant(health.voyage_status)}>
                Voyage
              </Badge>
              <Badge size="sm" variant={getStatusVariant(health.chroma_status)}>
                ChromaDB
              </Badge>
            </div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {health.document_count} documents
            </span>
          </div>
        ) : (
          <Badge variant="error" size="sm">
            Services indisponibles
          </Badge>
        )}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <button
          onClick={toggleDarkMode}
          className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700 transition-colors"
          aria-label={darkMode ? 'Activer le mode clair' : 'Activer le mode sombre'}
        >
          {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
      </div>
    </header>
  )
}

import { useState } from 'react'
import { Filter, X, ChevronDown, ChevronUp } from 'lucide-react'
import { useChatStore } from '../../stores/chatStore'
import Button from '../ui/Button'
import Input from '../ui/Input'
import Badge from '../ui/Badge'

export default function FilterPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const { filters, setFilters, clearFilters } = useChatStore()

  const [yearMin, setYearMin] = useState(filters.yearMin?.toString() || '')
  const [yearMax, setYearMax] = useState(filters.yearMax?.toString() || '')
  const [authorsInput, setAuthorsInput] = useState(filters.authors?.join(', ') || '')

  const hasFilters = filters.yearMin || filters.yearMax || (filters.authors && filters.authors.length > 0)

  const handleApply = () => {
    setFilters({
      yearMin: yearMin ? parseInt(yearMin) : undefined,
      yearMax: yearMax ? parseInt(yearMax) : undefined,
      authors: authorsInput ? authorsInput.split(',').map((a) => a.trim()).filter(Boolean) : undefined,
    })
    setIsOpen(false)
  }

  const handleClear = () => {
    setYearMin('')
    setYearMax('')
    setAuthorsInput('')
    clearFilters()
  }

  return (
    <div className="border-b border-gray-200 dark:border-gray-700">
      {/* Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2 flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4" />
          <span>Filtres</span>
          {hasFilters && (
            <Badge size="sm" variant="info">
              Actifs
            </Badge>
          )}
        </div>
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {/* Panel */}
      {isOpen && (
        <div className="px-4 py-3 bg-gray-50 dark:bg-gray-800/50 space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <Input
              label="Année min"
              type="number"
              placeholder="ex: 2020"
              value={yearMin}
              onChange={(e) => setYearMin(e.target.value)}
            />
            <Input
              label="Année max"
              type="number"
              placeholder="ex: 2024"
              value={yearMax}
              onChange={(e) => setYearMax(e.target.value)}
            />
          </div>
          <Input
            label="Auteurs (séparés par des virgules)"
            placeholder="ex: Vaswani, Devlin"
            value={authorsInput}
            onChange={(e) => setAuthorsInput(e.target.value)}
          />
          <div className="flex items-center justify-end gap-2 pt-2">
            <Button variant="ghost" size="sm" onClick={handleClear} leftIcon={<X className="h-4 w-4" />}>
              Effacer
            </Button>
            <Button size="sm" onClick={handleApply}>
              Appliquer
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

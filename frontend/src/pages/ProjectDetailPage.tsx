import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Plus,
  FileText,
  BookOpen,
  Download,
  Edit2,
  Trash2,
  Save,
  X,
  GripVertical,
} from 'lucide-react'
import {
  useProject,
  useUpdateProject,
  useAddProjectSource,
  useRemoveProjectSource,
  useCreateProjectSection,
  useUpdateProjectSection,
  useDeleteProjectSection,
  useExportProject,
} from '../hooks/useProjects'
import { useDocuments } from '../hooks/useDocuments'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Badge from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import Input from '../components/ui/Input'
import Spinner, { LoadingOverlay } from '../components/ui/Spinner'
import type { ProjectSourceInfo, ProjectSectionInfo, DocumentInfo } from '../api/types'

const STATUS_OPTIONS = [
  { value: 'draft', label: 'Brouillon' },
  { value: 'in_progress', label: 'En cours' },
  { value: 'completed', label: 'Terminé' },
]

const SECTION_TYPES = [
  { value: 'introduction', label: 'Introduction' },
  { value: 'literature_review', label: 'Revue de littérature' },
  { value: 'methods', label: 'Méthodologie' },
  { value: 'results', label: 'Résultats' },
  { value: 'discussion', label: 'Discussion' },
  { value: 'conclusion', label: 'Conclusion' },
  { value: 'abstract', label: 'Résumé' },
  { value: 'other', label: 'Autre' },
]

const RELEVANCE_OPTIONS = [
  { value: 'critical', label: 'Critique', color: 'text-red-600' },
  { value: 'high', label: 'Haute', color: 'text-orange-500' },
  { value: 'medium', label: 'Moyenne', color: 'text-yellow-500' },
  { value: 'low', label: 'Basse', color: 'text-gray-400' },
]

export default function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()

  const { data: project, isLoading, error } = useProject(projectId || null)
  const updateProject = useUpdateProject()
  const removeSource = useRemoveProjectSource()
  const updateSection = useUpdateProjectSection()
  const deleteSection = useDeleteProjectSection()
  const exportProject = useExportProject()

  const [editingTitle, setEditingTitle] = useState(false)
  const [titleInput, setTitleInput] = useState('')
  const [addSourceModalOpen, setAddSourceModalOpen] = useState(false)
  const [addSectionModalOpen, setAddSectionModalOpen] = useState(false)
  const [editingSectionId, setEditingSectionId] = useState<string | null>(null)
  const [sectionContent, setSectionContent] = useState('')

  if (isLoading) {
    return <LoadingOverlay message="Chargement du projet..." />
  }

  if (error || !project) {
    return (
      <div className="p-6">
        <Card padding="lg">
          <div className="text-center">
            <Badge variant="error">Projet introuvable</Badge>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Ce projet n'existe pas ou a été supprimé.
            </p>
            <Button variant="secondary" onClick={() => navigate('/projects')} className="mt-4">
              Retour aux projets
            </Button>
          </div>
        </Card>
      </div>
    )
  }

  const handleSaveTitle = async () => {
    if (!titleInput.trim()) return
    await updateProject.mutateAsync({
      projectId: project.id,
      data: { title: titleInput },
    })
    setEditingTitle(false)
  }

  const handleStatusChange = async (status: string) => {
    await updateProject.mutateAsync({
      projectId: project.id,
      data: { status: status as 'draft' | 'in_progress' | 'completed' },
    })
  }

  const handleRemoveSource = async (sourceId: string) => {
    await removeSource.mutateAsync({ projectId: project.id, sourceId })
  }

  const handleDeleteSection = async (sectionId: string) => {
    await deleteSection.mutateAsync({ projectId: project.id, sectionId })
  }

  const handleSaveSection = async (sectionId: string) => {
    await updateSection.mutateAsync({
      projectId: project.id,
      sectionId,
      data: { content: sectionContent },
    })
    setEditingSectionId(null)
    setSectionContent('')
  }

  const handleExport = async (format: string) => {
    await exportProject.mutateAsync({ projectId: project.id, format })
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <Button variant="ghost" onClick={() => navigate('/projects')} className="mt-1">
          <ArrowLeft className="h-5 w-5" />
        </Button>

        <div className="flex-1">
          {editingTitle ? (
            <div className="flex items-center gap-2">
              <Input
                value={titleInput}
                onChange={(e) => setTitleInput(e.target.value)}
                className="text-xl font-bold"
                autoFocus
              />
              <Button size="sm" onClick={handleSaveTitle}>
                <Save className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="ghost" onClick={() => setEditingTitle(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {project.title}
              </h1>
              <button
                onClick={() => {
                  setTitleInput(project.title)
                  setEditingTitle(true)
                }}
                className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <Edit2 className="h-4 w-4" />
              </button>
            </div>
          )}
          {project.description && (
            <p className="text-gray-500 dark:text-gray-400 mt-1">{project.description}</p>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* Status selector */}
          <select
            value={project.status}
            onChange={(e) => handleStatusChange(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>

          {/* Export */}
          <div className="relative group">
            <Button
              variant="secondary"
              leftIcon={<Download className="h-4 w-4" />}
              disabled={exportProject.isPending}
            >
              {exportProject.isPending ? <Spinner size="sm" /> : 'Exporter'}
            </Button>
            <div className="absolute right-0 top-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => handleExport('docx')}
                className="block w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded-t-lg"
              >
                Word (.docx)
              </button>
              <button
                onClick={() => handleExport('md')}
                className="block w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded-b-lg"
              >
                Markdown (.md)
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Sources */}
        <div className="lg:col-span-1">
          <Card padding="none">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Sources ({project.sources.length})
              </h2>
              <Button size="sm" onClick={() => setAddSourceModalOpen(true)}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {project.sources.length === 0 ? (
              <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                <p className="text-sm">Aucune source ajoutée</p>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setAddSourceModalOpen(true)}
                  className="mt-2"
                >
                  Ajouter une source
                </Button>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700 max-h-[500px] overflow-y-auto">
                {project.sources.map((source) => (
                  <SourceItem
                    key={source.id}
                    source={source}
                    onRemove={() => handleRemoveSource(source.id)}
                  />
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Sections */}
        <div className="lg:col-span-2">
          <Card padding="none">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Sections ({project.sections.length})
              </h2>
              <Button size="sm" onClick={() => setAddSectionModalOpen(true)}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>

            {project.sections.length === 0 ? (
              <div className="p-6 text-center text-gray-500 dark:text-gray-400">
                <p className="text-sm">Aucune section créée</p>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => setAddSectionModalOpen(true)}
                  className="mt-2"
                >
                  Créer une section
                </Button>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {project.sections
                  .sort((a, b) => a.section_order - b.section_order)
                  .map((section) => (
                    <SectionItem
                      key={section.id}
                      section={section}
                      isEditing={editingSectionId === section.id}
                      content={sectionContent}
                      onEdit={() => {
                        setEditingSectionId(section.id)
                        setSectionContent(section.content || '')
                      }}
                      onContentChange={setSectionContent}
                      onSave={() => handleSaveSection(section.id)}
                      onCancel={() => {
                        setEditingSectionId(null)
                        setSectionContent('')
                      }}
                      onDelete={() => handleDeleteSection(section.id)}
                    />
                  ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Modal ajout source */}
      <AddSourceModal
        isOpen={addSourceModalOpen}
        onClose={() => setAddSourceModalOpen(false)}
        projectId={project.id}
        existingSourceIds={project.sources.map((s) => s.document_id)}
      />

      {/* Modal création section */}
      <AddSectionModal
        isOpen={addSectionModalOpen}
        onClose={() => setAddSectionModalOpen(false)}
        projectId={project.id}
      />
    </div>
  )
}

// Composant source
function SourceItem({
  source,
  onRemove,
}: {
  source: ProjectSourceInfo
  onRemove: () => void
}) {
  const relevance = RELEVANCE_OPTIONS.find((r) => r.value === source.relevance)

  return (
    <div className="p-3 hover:bg-gray-50 dark:hover:bg-gray-700/50 group">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 dark:text-gray-100 text-sm truncate">
            {source.document_title}
          </p>
          {source.document_authors && (
            <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
              {source.document_authors}
              {source.document_year && ` (${source.document_year})`}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs ${relevance?.color || 'text-gray-400'}`}>
            {relevance?.label}
          </span>
          <button
            onClick={onRemove}
            className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
          >
            <Trash2 className="h-3 w-3" />
          </button>
        </div>
      </div>
      {source.notes && (
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1 italic">{source.notes}</p>
      )}
    </div>
  )
}

// Composant section
function SectionItem({
  section,
  isEditing,
  content,
  onEdit,
  onContentChange,
  onSave,
  onCancel,
  onDelete,
}: {
  section: ProjectSectionInfo
  isEditing: boolean
  content: string
  onEdit: () => void
  onContentChange: (c: string) => void
  onSave: () => void
  onCancel: () => void
  onDelete: () => void
}) {
  const sectionType = SECTION_TYPES.find((s) => s.value === section.section_type)

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <GripVertical className="h-4 w-4 text-gray-300 cursor-grab" />
          <Badge variant="default">{sectionType?.label || section.section_type}</Badge>
          {section.title && (
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {section.title}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400">{section.word_count} mots</span>
          {!isEditing && (
            <>
              <button
                onClick={onEdit}
                className="p-1 text-gray-400 hover:text-primary-500 transition-colors"
              >
                <Edit2 className="h-4 w-4" />
              </button>
              <button
                onClick={onDelete}
                className="p-1 text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {isEditing ? (
        <div className="space-y-3">
          <textarea
            value={content}
            onChange={(e) => onContentChange(e.target.value)}
            rows={10}
            className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 text-sm font-mono"
            placeholder="Rédigez le contenu de cette section en Markdown..."
          />
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="secondary" onClick={onCancel}>
              Annuler
            </Button>
            <Button size="sm" onClick={onSave}>
              Enregistrer
            </Button>
          </div>
        </div>
      ) : (
        <div
          className="prose prose-sm dark:prose-invert max-w-none text-gray-600 dark:text-gray-400 cursor-pointer"
          onClick={onEdit}
        >
          {section.content ? (
            <p className="line-clamp-3">{section.content}</p>
          ) : (
            <p className="italic text-gray-400">Cliquez pour ajouter du contenu...</p>
          )}
        </div>
      )}
    </div>
  )
}

// Modal ajout source
function AddSourceModal({
  isOpen,
  onClose,
  projectId,
  existingSourceIds,
}: {
  isOpen: boolean
  onClose: () => void
  projectId: string
  existingSourceIds: string[]
}) {
  const [search, setSearch] = useState('')
  const [selectedDoc, setSelectedDoc] = useState<DocumentInfo | null>(null)
  const [notes, setNotes] = useState('')
  const [relevance, setRelevance] = useState<'low' | 'medium' | 'high' | 'critical'>('medium')

  const { data: documents } = useDocuments({ limit: 100, status: 'indexed' })
  const addSource = useAddProjectSource()

  const availableDocs = documents?.documents.filter(
    (d) => !existingSourceIds.includes(d.id) && d.title.toLowerCase().includes(search.toLowerCase())
  )

  const handleAdd = async () => {
    if (!selectedDoc) return
    await addSource.mutateAsync({
      projectId,
      data: {
        document_id: selectedDoc.id,
        notes: notes || null,
        relevance,
      },
    })
    onClose()
    setSelectedDoc(null)
    setNotes('')
    setRelevance('medium')
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Ajouter une source">
      <div className="space-y-4">
        <Input
          placeholder="Rechercher un document..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <div className="max-h-48 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg">
          {availableDocs?.length === 0 ? (
            <p className="p-4 text-center text-gray-500 text-sm">Aucun document disponible</p>
          ) : (
            availableDocs?.map((doc) => (
              <button
                key={doc.id}
                onClick={() => setSelectedDoc(doc)}
                className={`w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700/50 border-b last:border-b-0 border-gray-100 dark:border-gray-700 ${
                  selectedDoc?.id === doc.id ? 'bg-primary-50 dark:bg-primary-900/20' : ''
                }`}
              >
                <p className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">
                  {doc.title}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {doc.authors || 'Auteurs inconnus'}
                  {doc.year && ` (${doc.year})`}
                </p>
              </button>
            ))
          )}
        </div>

        {selectedDoc && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Pertinence
              </label>
              <select
                value={relevance}
                onChange={(e) => setRelevance(e.target.value as typeof relevance)}
                className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
              >
                {RELEVANCE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Notes (optionnel)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={2}
                className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
                placeholder="Notes sur cette source..."
              />
            </div>
          </>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button onClick={handleAdd} disabled={!selectedDoc || addSource.isPending}>
            {addSource.isPending ? <Spinner size="sm" /> : 'Ajouter'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

// Modal création section
function AddSectionModal({
  isOpen,
  onClose,
  projectId,
}: {
  isOpen: boolean
  onClose: () => void
  projectId: string
}) {
  const [sectionType, setSectionType] = useState('introduction')
  const [title, setTitle] = useState('')

  const createSection = useCreateProjectSection()

  const handleCreate = async () => {
    await createSection.mutateAsync({
      projectId,
      data: {
        section_type: sectionType,
        title: title || null,
      },
    })
    onClose()
    setSectionType('introduction')
    setTitle('')
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Nouvelle section">
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Type de section
          </label>
          <select
            value={sectionType}
            onChange={(e) => setSectionType(e.target.value)}
            className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg"
          >
            {SECTION_TYPES.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Titre personnalisé (optionnel)
          </label>
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ex: Introduction générale"
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button onClick={handleCreate} disabled={createSection.isPending}>
            {createSection.isPending ? <Spinner size="sm" /> : 'Créer'}
          </Button>
        </div>
      </div>
    </Modal>
  )
}

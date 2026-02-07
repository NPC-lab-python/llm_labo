import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FolderOpen, Search } from 'lucide-react'
import { useProjects, useCreateProject, useDeleteProject } from '../hooks/useProjects'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import Input from '../components/ui/Input'
import Badge from '../components/ui/Badge'
import Modal from '../components/ui/Modal'
import Spinner, { LoadingOverlay } from '../components/ui/Spinner'
import type { ProjectInfo } from '../api/types'

const STATUS_LABELS: Record<string, { label: string; variant: 'default' | 'warning' | 'success' }> = {
  draft: { label: 'Brouillon', variant: 'default' },
  in_progress: { label: 'En cours', variant: 'warning' },
  completed: { label: 'Terminé', variant: 'success' },
}

export default function ProjectsPage() {
  const navigate = useNavigate()
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<ProjectInfo | null>(null)
  const [newProject, setNewProject] = useState({ title: '', description: '' })

  const { data, isLoading, error } = useProjects(statusFilter || undefined)
  const createMutation = useCreateProject()
  const deleteMutation = useDeleteProject()

  // Filtrer par recherche côté client
  const filteredProjects = data?.projects.filter((p) =>
    p.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCreate = async () => {
    if (!newProject.title.trim()) return
    try {
      const created = await createMutation.mutateAsync({
        title: newProject.title,
        description: newProject.description || null,
      })
      setCreateModalOpen(false)
      setNewProject({ title: '', description: '' })
      navigate(`/projects/${created.id}`)
    } catch {
      // Erreur gérée par React Query
    }
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteMutation.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Projets de Rédaction
          </h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Gérez vos projets d'articles scientifiques
          </p>
        </div>
        <Button onClick={() => setCreateModalOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
          Nouveau Projet
        </Button>
      </div>

      {/* Filtres */}
      <Card padding="md">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <Input
              placeholder="Rechercher un projet..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="h-4 w-4" />}
            />
          </div>
          <div className="flex gap-2">
            {['', 'draft', 'in_progress', 'completed'].map((status) => (
              <button
                key={status || 'all'}
                type="button"
                onClick={() => setStatusFilter(status)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  statusFilter === status
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400'
                    : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700'
                }`}
              >
                {status === '' && 'Tous'}
                {status === 'draft' && 'Brouillons'}
                {status === 'in_progress' && 'En cours'}
                {status === 'completed' && 'Terminés'}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Liste des projets */}
      {isLoading ? (
        <LoadingOverlay message="Chargement des projets..." />
      ) : error ? (
        <Card padding="lg">
          <div className="text-center">
            <Badge variant="error">Erreur de chargement</Badge>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Impossible de charger les projets
            </p>
          </div>
        </Card>
      ) : filteredProjects && filteredProjects.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredProjects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={() => navigate(`/projects/${project.id}`)}
              onDelete={() => setDeleteTarget(project)}
            />
          ))}
        </div>
      ) : (
        <Card padding="lg">
          <div className="text-center py-12">
            <FolderOpen className="h-16 w-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
              Aucun projet
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {searchQuery
                ? 'Aucun projet ne correspond à votre recherche'
                : 'Créez votre premier projet de rédaction'}
            </p>
            {!searchQuery && (
              <Button onClick={() => setCreateModalOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
                Créer un projet
              </Button>
            )}
          </div>
        </Card>
      )}

      {/* Modal création */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Nouveau Projet"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Titre du projet *
            </label>
            <Input
              value={newProject.title}
              onChange={(e) => setNewProject((p) => ({ ...p, title: e.target.value }))}
              placeholder="Ex: Revue de littérature sur l'IA"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description (optionnel)
            </label>
            <textarea
              value={newProject.description}
              onChange={(e) => setNewProject((p) => ({ ...p, description: e.target.value }))}
              placeholder="Décrivez brièvement l'objectif de ce projet..."
              rows={3}
              className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setCreateModalOpen(false)}>
              Annuler
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newProject.title.trim() || createMutation.isPending}
            >
              {createMutation.isPending ? <Spinner size="sm" /> : 'Créer'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Modal suppression */}
      <Modal
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Supprimer le projet"
      >
        <div className="space-y-4">
          <p className="text-gray-600 dark:text-gray-400">
            Êtes-vous sûr de vouloir supprimer le projet{' '}
            <strong className="text-gray-900 dark:text-gray-100">{deleteTarget?.title}</strong> ?
          </p>
          <p className="text-sm text-red-600 dark:text-red-400">
            Cette action est irréversible. Toutes les sources et sections seront supprimées.
          </p>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
              Annuler
            </Button>
            <Button variant="danger" onClick={handleDelete} disabled={deleteMutation.isPending}>
              {deleteMutation.isPending ? <Spinner size="sm" /> : 'Supprimer'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

// Composant carte projet
function ProjectCard({
  project,
  onClick,
  onDelete,
}: {
  project: ProjectInfo
  onClick: () => void
  onDelete: () => void
}) {
  const status = STATUS_LABELS[project.status] || STATUS_LABELS.draft

  return (
    <Card
      padding="md"
      className="cursor-pointer hover:shadow-lg transition-shadow group"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <Badge variant={status.variant}>{status.label}</Badge>
        <button
          onClick={(e) => {
            e.stopPropagation()
            onDelete()
          }}
          className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition-all"
          title="Supprimer"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
        </button>
      </div>

      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1 line-clamp-2">
        {project.title}
      </h3>

      {project.description && (
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-3 line-clamp-2">
          {project.description}
        </p>
      )}

      <div className="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500 mt-auto pt-3 border-t border-gray-100 dark:border-gray-700">
        <span>{project.sources_count} source{project.sources_count !== 1 ? 's' : ''}</span>
        <span>{project.sections_count} section{project.sections_count !== 1 ? 's' : ''}</span>
        <span className="ml-auto">
          {new Date(project.updated_at).toLocaleDateString('fr-FR')}
        </span>
      </div>
    </Card>
  )
}

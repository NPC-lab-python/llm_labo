import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  getProjects,
  getProject,
  createProject,
  updateProject,
  deleteProject,
  addProjectSource,
  updateProjectSource,
  removeProjectSource,
  createProjectSection,
  updateProjectSection,
  deleteProjectSection,
  exportProject,
} from '../api/endpoints'
import type { ProjectCreate, ProjectUpdate, ProjectSourceCreate, ProjectSectionCreate, ProjectSectionUpdate } from '../api/types'

export function useProjects(status?: string) {
  return useQuery({
    queryKey: ['projects', status],
    queryFn: () => getProjects(status),
  })
}

export function useProject(projectId: string | null) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
  })
}

export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: ProjectCreate) => createProject(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUpdateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: ProjectUpdate }) =>
      updateProject(projectId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })
}

export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

// === Sources ===

export function useAddProjectSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: ProjectSourceCreate }) =>
      addProjectSource(projectId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUpdateProjectSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      sourceId,
      data,
    }: {
      projectId: string
      sourceId: string
      data: { notes?: string; highlights?: string[]; relevance?: string }
    }) => updateProjectSource(projectId, sourceId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })
}

export function useRemoveProjectSource() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, sourceId }: { projectId: string; sourceId: string }) =>
      removeProjectSource(projectId, sourceId),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

// === Sections ===

export function useCreateProjectSection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, data }: { projectId: string; data: ProjectSectionCreate }) =>
      createProjectSection(projectId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUpdateProjectSection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      projectId,
      sectionId,
      data,
    }: {
      projectId: string
      sectionId: string
      data: ProjectSectionUpdate
    }) => updateProjectSection(projectId, sectionId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    },
  })
}

export function useDeleteProjectSection() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ projectId, sectionId }: { projectId: string; sectionId: string }) =>
      deleteProjectSection(projectId, sectionId),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

// === Export ===

export function useExportProject() {
  return useMutation({
    mutationFn: async ({
      projectId,
      format = 'docx',
    }: {
      projectId: string
      format?: string
    }) => {
      const blob = await exportProject(projectId, format)
      // Télécharger le fichier
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `projet_${projectId}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    },
  })
}

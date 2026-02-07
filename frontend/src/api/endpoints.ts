import { apiClient } from './client'
import type {
  QueryRequest,
  QueryResponse,
  IndexRequest,
  IndexResponse,
  BatchIndexRequest,
  BatchIndexResponse,
  HealthResponse,
  DocumentListResponse,
  MetadataQualityStats,
  ReindexResponse,
  ResetResponse,
  SummaryResponse,
  ProjectListResponse,
  ProjectInfo,
  ProjectDetail,
  ProjectCreate,
  ProjectUpdate,
  ProjectSourceInfo,
  ProjectSourceCreate,
  ProjectSectionInfo,
  ProjectSectionCreate,
  ProjectSectionUpdate,
  ReferenceListResponse,
} from './types'

// === Requêtes ===

export async function postQuery(data: QueryRequest): Promise<QueryResponse> {
  const response = await apiClient.post<QueryResponse>('/query', data)
  return response.data
}

// === Indexation ===

export async function indexDocument(data: IndexRequest): Promise<IndexResponse> {
  const response = await apiClient.post<IndexResponse>('/index', data)
  return response.data
}

export async function indexBatch(data: BatchIndexRequest): Promise<BatchIndexResponse> {
  const response = await apiClient.post<BatchIndexResponse>('/index/batch', data)
  return response.data
}

export async function reindexEmbeddings(documentId?: string): Promise<ReindexResponse> {
  const response = await apiClient.post<ReindexResponse>('/index/reindex', null, {
    params: documentId ? { document_id: documentId } : undefined,
  })
  return response.data
}

export async function resetDatabases(): Promise<ResetResponse> {
  const response = await apiClient.post<ResetResponse>('/index/reset')
  return response.data
}

export async function uploadPdf(file: File): Promise<IndexResponse> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post<IndexResponse>('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

// === Documents ===

export async function getDocuments(params?: {
  page?: number
  limit?: number
  search?: string
  status?: string
}): Promise<DocumentListResponse> {
  const response = await apiClient.get<DocumentListResponse>('/documents', { params })
  return response.data
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/documents/${id}`)
}

// === Santé et Statistiques ===

export async function getHealth(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>('/health')
  return response.data
}

export async function getStats(): Promise<MetadataQualityStats> {
  const response = await apiClient.get<MetadataQualityStats>('/stats')
  return response.data
}

// === PDF ===

export function getDocumentPdfUrl(documentId: string, page?: number): string {
  const base = `/api/v1/documents/${documentId}/pdf`
  return page ? `${base}#page=${page}` : base
}

export async function generateSummary(documentId: string): Promise<SummaryResponse> {
  const response = await apiClient.post<SummaryResponse>(`/documents/${documentId}/summary`)
  return response.data
}

// === Références ===

export async function getDocumentReferences(documentId: string): Promise<ReferenceListResponse> {
  const response = await apiClient.get<ReferenceListResponse>(`/documents/${documentId}/references`)
  return response.data
}

export function getDocumentBibtexUrl(documentId: string): string {
  return `/api/v1/documents/${documentId}/references/bibtex`
}

// === Projets ===

export async function getProjects(status?: string): Promise<ProjectListResponse> {
  const response = await apiClient.get<ProjectListResponse>('/projects', {
    params: status ? { status } : undefined,
  })
  return response.data
}

export async function getProject(projectId: string): Promise<ProjectDetail> {
  const response = await apiClient.get<ProjectDetail>(`/projects/${projectId}`)
  return response.data
}

export async function createProject(data: ProjectCreate): Promise<ProjectInfo> {
  const response = await apiClient.post<ProjectInfo>('/projects', data)
  return response.data
}

export async function updateProject(projectId: string, data: ProjectUpdate): Promise<ProjectInfo> {
  const response = await apiClient.put<ProjectInfo>(`/projects/${projectId}`, data)
  return response.data
}

export async function deleteProject(projectId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}`)
}

// === Sources de projet ===

export async function addProjectSource(projectId: string, data: ProjectSourceCreate): Promise<ProjectSourceInfo> {
  const response = await apiClient.post<ProjectSourceInfo>(`/projects/${projectId}/sources`, data)
  return response.data
}

export async function updateProjectSource(
  projectId: string,
  sourceId: string,
  data: { notes?: string; highlights?: string[]; relevance?: string }
): Promise<ProjectSourceInfo> {
  const response = await apiClient.put<ProjectSourceInfo>(`/projects/${projectId}/sources/${sourceId}`, data)
  return response.data
}

export async function removeProjectSource(projectId: string, sourceId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/sources/${sourceId}`)
}

// === Sections de projet ===

export async function createProjectSection(projectId: string, data: ProjectSectionCreate): Promise<ProjectSectionInfo> {
  const response = await apiClient.post<ProjectSectionInfo>(`/projects/${projectId}/sections`, data)
  return response.data
}

export async function updateProjectSection(
  projectId: string,
  sectionId: string,
  data: ProjectSectionUpdate
): Promise<ProjectSectionInfo> {
  const response = await apiClient.put<ProjectSectionInfo>(`/projects/${projectId}/sections/${sectionId}`, data)
  return response.data
}

export async function deleteProjectSection(projectId: string, sectionId: string): Promise<void> {
  await apiClient.delete(`/projects/${projectId}/sections/${sectionId}`)
}

// === Export ===

export function getProjectExportUrl(projectId: string, format: string = 'docx'): string {
  return `/api/v1/projects/${projectId}/export?format=${format}`
}

export async function exportProject(
  projectId: string,
  format: string = 'docx',
  includeBibliography: boolean = true
): Promise<Blob> {
  const response = await apiClient.post(
    `/projects/${projectId}/export`,
    { format, include_bibliography: includeBibliography, citation_style: 'apa' },
    { responseType: 'blob' }
  )
  return response.data
}

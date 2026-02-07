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

// Types TypeScript correspondant aux schemas Pydantic

// === Requêtes ===

export interface QueryRequest {
  question: string
  top_k?: number
  year_min?: number | null
  year_max?: number | null
  authors?: string[] | null
}

export interface IndexRequest {
  file_path: string
  title?: string | null
  authors?: string[] | null
  year?: number | null
}

export interface BatchIndexRequest {
  folder_path: string
}

// === Réponses ===

export interface Source {
  document_id: string
  title: string
  authors: string | null
  year: number | null
  page: number | null
  relevance_score: number
}

export interface QueryResponse {
  answer: string
  sources: Source[]
  processing_time_ms: number
}

export interface DocumentInfo {
  id: string
  title: string
  authors: string | null
  year: number | null
  page_count: number | null
  chunk_count: number
  status: 'pending' | 'indexed' | 'error'
  indexed_at: string | null
}

export interface IndexResponse {
  document_id: string
  title: string
  chunks_count: number
  status: string
}

export interface BatchIndexResponse {
  processed: number
  errors: string[]
  documents: IndexResponse[]
}

export interface HealthResponse {
  status: string
  chroma_status: string
  claude_status: string
  voyage_status: string
  document_count: number
}

export interface DocumentListResponse {
  documents: DocumentInfo[]
  total: number
  page: number
  limit: number
}

export interface MetadataQualityStats {
  total_documents: number
  average_score: float
  score_distribution: Record<string, number>
  missing_fields: Record<string, number>
  low_quality_count: number
  documents_needing_review: Array<{
    id: string
    title: string
    score: number
  }>
}

// === Types pour le Chat ===

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  processingTime?: number
  timestamp: Date
}

export interface ChatFilters {
  yearMin?: number
  yearMax?: number
  authors?: string[]
}

// Alias pour clarté
type float = number

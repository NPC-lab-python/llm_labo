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
  section: string | null  // Section normalisée (introduction, methods, results, etc.)
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

// === Types pour la réindexation ===

export interface ReindexResponse {
  reindexed: number
  total: number
  errors: string[]
  message: string
}

export interface ResetResponse {
  status: string
  documents_deleted: number
  chunks_deleted: number
  message: string
}

export interface SummaryResponse {
  document_id: string
  title: string
  summary: string
}

// === Types pour les Projets ===

export interface ProjectInfo {
  id: string
  title: string
  description: string | null
  status: 'draft' | 'in_progress' | 'completed'
  sources_count: number
  sections_count: number
  created_at: string
  updated_at: string
}

export interface ProjectSourceInfo {
  id: string
  document_id: string
  document_title: string
  document_authors: string | null
  document_year: number | null
  notes: string | null
  highlights: string[] | null
  relevance: 'low' | 'medium' | 'high' | 'critical'
  added_at: string
}

export interface ProjectSectionInfo {
  id: string
  section_type: string
  section_order: number
  title: string | null
  content: string | null
  cited_sources: string[] | null
  word_count: number
  status: 'draft' | 'review' | 'final'
  updated_at: string
}

export interface ProjectDetail {
  id: string
  title: string
  description: string | null
  status: 'draft' | 'in_progress' | 'completed'
  sources: ProjectSourceInfo[]
  sections: ProjectSectionInfo[]
  created_at: string
  updated_at: string
}

export interface ProjectListResponse {
  projects: ProjectInfo[]
  total: number
}

export interface ProjectCreate {
  title: string
  description?: string | null
}

export interface ProjectUpdate {
  title?: string
  description?: string
  status?: 'draft' | 'in_progress' | 'completed'
}

export interface ProjectSourceCreate {
  document_id: string
  notes?: string | null
  relevance?: 'low' | 'medium' | 'high' | 'critical'
}

export interface ProjectSectionCreate {
  section_type: string
  title?: string | null
  content?: string | null
}

export interface ProjectSectionUpdate {
  title?: string | null
  content?: string | null
  section_order?: number
  status?: 'draft' | 'review' | 'final'
}

// === Types pour les Références ===

export interface ReferenceInfo {
  id: string
  document_id: string
  title: string | null
  authors: string | null
  year: number | null
  journal: string | null
  volume: string | null
  pages: string | null
  doi: string | null
  url: string | null
  bibtex: string | null
  apa_citation: string | null
}

export interface ReferenceListResponse {
  document_id: string
  document_title: string
  references: ReferenceInfo[]
  total: number
}

// Alias pour clarté
type float = number

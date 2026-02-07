"""Schemas Pydantic pour l'API."""

from datetime import datetime
from pydantic import BaseModel, Field


# === Requêtes ===


class QueryRequest(BaseModel):
    """Requête de recherche."""

    question: str = Field(..., min_length=3, description="Question à poser")
    top_k: int = Field(default=5, ge=1, le=20, description="Nombre de résultats")
    year_min: int | None = Field(default=None, description="Année minimum")
    year_max: int | None = Field(default=None, description="Année maximum")
    authors: list[str] | None = Field(default=None, description="Filtrer par auteurs")


class IndexRequest(BaseModel):
    """Requête d'indexation d'un fichier."""

    file_path: str = Field(..., description="Chemin vers le fichier PDF")
    title: str | None = Field(default=None, description="Titre du document")
    authors: list[str] | None = Field(default=None, description="Auteurs")
    year: int | None = Field(default=None, description="Année de publication")


class BatchIndexRequest(BaseModel):
    """Requête d'indexation batch."""

    folder_path: str = Field(..., description="Chemin vers le dossier de PDFs")


# === Réponses ===


class Source(BaseModel):
    """Source citée dans une réponse."""

    document_id: str
    title: str
    authors: str | None = None
    year: int | None = None
    page: int | None = None
    section: str | None = None  # Section normalisée (introduction, methods, results, etc.)
    relevance_score: float


class QueryResponse(BaseModel):
    """Réponse à une requête de recherche."""

    answer: str
    sources: list[Source]
    processing_time_ms: int


class DocumentInfo(BaseModel):
    """Informations sur un document."""

    id: str
    title: str
    authors: str | None = None
    year: int | None = None
    page_count: int | None = None
    chunk_count: int = 0
    status: str
    indexed_at: datetime | None = None


class IndexResponse(BaseModel):
    """Réponse à une requête d'indexation."""

    document_id: str
    title: str
    chunks_count: int
    status: str


class BatchIndexResponse(BaseModel):
    """Réponse à une indexation batch."""

    processed: int
    errors: list[str]
    documents: list[IndexResponse]


class HealthResponse(BaseModel):
    """État de santé du système."""

    status: str
    chroma_status: str
    claude_status: str
    voyage_status: str
    document_count: int


class DocumentListResponse(BaseModel):
    """Liste paginée de documents."""

    documents: list[DocumentInfo]
    total: int
    page: int
    limit: int


class MetadataQualityStats(BaseModel):
    """Statistiques de qualité des métadonnées."""

    total_documents: int
    average_score: float
    score_distribution: dict[str, int]  # Excellent/Good/Fair/Poor
    missing_fields: dict[str, int]  # Champs manquants par type
    low_quality_count: int
    documents_needing_review: list[dict]  # Top documents à corriger

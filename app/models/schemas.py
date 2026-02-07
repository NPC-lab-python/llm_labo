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


# === Références bibliographiques ===


class ReferenceInfo(BaseModel):
    """Référence bibliographique extraite."""

    id: str
    document_id: str
    title: str | None = None
    authors: str | None = None
    year: int | None = None
    journal: str | None = None
    volume: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    bibtex: str | None = None
    apa_citation: str | None = None  # Citation formatée APA


class ReferenceListResponse(BaseModel):
    """Liste des références d'un document."""

    document_id: str
    document_title: str
    references: list[ReferenceInfo]
    total: int


# === Projets de recherche ===


class ProjectCreate(BaseModel):
    """Création d'un projet."""

    title: str = Field(..., min_length=3, description="Titre du projet")
    description: str | None = Field(default=None, description="Description du projet")


class ProjectUpdate(BaseModel):
    """Mise à jour d'un projet."""

    title: str | None = None
    description: str | None = None
    status: str | None = None  # draft, in_progress, completed


class ProjectSourceCreate(BaseModel):
    """Ajout d'une source à un projet."""

    document_id: str = Field(..., description="ID du document à ajouter")
    notes: str | None = None
    relevance: str = Field(default="medium", description="Pertinence: low, medium, high, critical")


class ProjectSourceUpdate(BaseModel):
    """Mise à jour d'une source de projet."""

    notes: str | None = None
    highlights: list[str] | None = None  # Extraits sauvegardés
    relevance: str | None = None


class ProjectSectionCreate(BaseModel):
    """Création d'une section de projet."""

    section_type: str = Field(..., description="Type: introduction, literature_review, methods, results, discussion, conclusion")
    title: str | None = None
    content: str | None = None


class ProjectSectionUpdate(BaseModel):
    """Mise à jour d'une section."""

    title: str | None = None
    content: str | None = None
    section_order: int | None = None
    status: str | None = None  # draft, review, final


class ProjectSourceInfo(BaseModel):
    """Informations sur une source de projet."""

    id: str
    document_id: str
    document_title: str
    document_authors: str | None = None
    document_year: int | None = None
    notes: str | None = None
    highlights: list[str] | None = None
    relevance: str
    added_at: datetime


class ProjectSectionInfo(BaseModel):
    """Informations sur une section de projet."""

    id: str
    section_type: str
    section_order: int
    title: str | None = None
    content: str | None = None
    cited_sources: list[str] | None = None
    word_count: int
    status: str
    updated_at: datetime


class ProjectInfo(BaseModel):
    """Informations complètes sur un projet."""

    id: str
    title: str
    description: str | None = None
    status: str
    sources_count: int = 0
    sections_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectDetail(BaseModel):
    """Détails complets d'un projet avec sources et sections."""

    id: str
    title: str
    description: str | None = None
    status: str
    sources: list[ProjectSourceInfo]
    sections: list[ProjectSectionInfo]
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Liste des projets."""

    projects: list[ProjectInfo]
    total: int


class ExportRequest(BaseModel):
    """Demande d'export d'un projet."""

    format: str = Field(default="docx", description="Format: docx, markdown, pdf")
    include_bibliography: bool = Field(default=True, description="Inclure la bibliographie")
    citation_style: str = Field(default="apa", description="Style: apa, ieee, vancouver")


class ExportResponse(BaseModel):
    """Réponse d'export."""

    filename: str
    format: str
    download_url: str

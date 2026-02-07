"""Modèles SQLAlchemy pour la base de données."""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    DateTime,
    ForeignKey,
    create_engine,
    Index,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import settings

Base = declarative_base()


class Document(Base):
    """Table des documents indexés."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    title = Column(Text, nullable=False)
    authors = Column(Text)  # JSON array
    publication_year = Column(Integer)
    source_type = Column(String(50), default="article")
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False, unique=True)
    page_count = Column(Integer)
    language = Column(String(10), default="fr")
    abstract = Column(Text)
    keywords = Column(Text)  # JSON array
    doi = Column(String(100))  # Digital Object Identifier
    journal = Column(Text)  # Nom du journal/conférence
    extraction_method = Column(String(20), default="pymupdf")  # "pymupdf" ou "grobid"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    indexed_at = Column(DateTime)
    status = Column(String(20), default="pending")
    metadata_quality_score = Column(Float, default=0.0)  # Score de 0 à 1

    # Relations
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_documents_status", "status"),
        Index("idx_documents_hash", "file_hash"),
    )


class Chunk(Base):
    """Table des chunks (référence vers ChromaDB)."""

    __tablename__ = "chunks"

    id = Column(String(36), primary_key=True)  # Même ID que dans ChromaDB
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer)
    section_title = Column(Text)
    char_start = Column(Integer)
    char_end = Column(Integer)
    token_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    document = relationship("Document", back_populates="chunks")

    __table_args__ = (
        Index("idx_chunks_document", "document_id"),
        Index("idx_chunks_page", "page_number"),
    )


class Reference(Base):
    """Table des références bibliographiques extraites des documents."""

    __tablename__ = "references"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    # Champs bibliographiques
    ref_title = Column(Text)
    ref_authors = Column(Text)  # JSON array
    ref_year = Column(Integer)
    ref_journal = Column(Text)
    ref_volume = Column(String(20))
    ref_pages = Column(String(50))
    ref_doi = Column(String(100))
    ref_url = Column(Text)
    # Format BibTeX généré
    bibtex = Column(Text)
    # Position dans le document
    ref_index = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    document = relationship("Document", backref="references")

    __table_args__ = (
        Index("idx_references_document", "document_id"),
    )


class Project(Base):
    """Table des projets de recherche/rédaction."""

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    title = Column(Text, nullable=False)
    description = Column(Text)
    status = Column(String(20), default="draft")  # draft, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    sources = relationship("ProjectSource", back_populates="project", cascade="all, delete-orphan")
    sections = relationship("ProjectSection", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_status", "status"),
    )


class ProjectSource(Base):
    """Table des sources associées à un projet."""

    __tablename__ = "project_sources"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    # Notes et annotations
    notes = Column(Text)
    highlights = Column(Text)  # JSON array d'extraits sauvegardés
    relevance = Column(String(20), default="medium")  # low, medium, high, critical
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="sources")
    document = relationship("Document")

    __table_args__ = (
        Index("idx_project_sources_project", "project_id"),
        Index("idx_project_sources_document", "document_id"),
    )


class ProjectSection(Base):
    """Table des sections rédigées d'un projet."""

    __tablename__ = "project_sections"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    # Type de section
    section_type = Column(String(50), nullable=False)  # introduction, literature_review, methods, results, discussion, conclusion
    section_order = Column(Integer, default=0)
    title = Column(Text)
    # Contenu
    content = Column(Text)  # Texte rédigé (Markdown)
    cited_sources = Column(Text)  # JSON array des IDs de sources citées
    # Métadonnées
    word_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")  # draft, review, final
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    project = relationship("Project", back_populates="sections")

    __table_args__ = (
        Index("idx_project_sections_project", "project_id"),
        Index("idx_project_sections_type", "section_type"),
    )


# Création du moteur et de la session
engine = create_engine(f"sqlite:///{settings.sqlite_path}", echo=settings.debug)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialise la base de données."""
    settings.ensure_directories()
    Base.metadata.create_all(bind=engine)


def get_db():
    """Générateur de session pour FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

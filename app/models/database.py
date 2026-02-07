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

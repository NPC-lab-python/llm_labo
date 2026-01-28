"""Service d'indexation des documents PDF."""

import json
import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger
from sqlalchemy.orm import Session
from tqdm import tqdm

from app.core.pdf_extractor import pdf_extractor, PDFContent
from app.core.chunker import chunker
from app.core.embedder import get_embedder
from app.core.retriever import get_retriever
from app.models.database import Document, Chunk
from app.models.schemas import IndexResponse, BatchIndexResponse


class IndexingService:
    """Service d'indexation des documents."""

    def index_document(
        self,
        db: Session,
        file_path: str | Path,
        title: str | None = None,
        authors: list[str] | None = None,
        year: int | None = None,
    ) -> IndexResponse:
        """
        Indexe un document PDF.

        Args:
            db: Session SQLAlchemy.
            file_path: Chemin vers le fichier PDF.
            title: Titre (optionnel, extrait du PDF sinon).
            authors: Auteurs (optionnel).
            year: Année de publication (optionnel).

        Returns:
            IndexResponse avec les informations du document indexé.
        """
        file_path = Path(file_path)
        logger.info(f"Indexation du document: {file_path}")

        # Extraction du PDF
        pdf_content = pdf_extractor.extract(file_path)

        # Vérification de déduplication
        existing = db.query(Document).filter(
            Document.file_hash == pdf_content.metadata.file_hash
        ).first()

        if existing:
            logger.warning(f"Document déjà indexé: {existing.title}")
            return IndexResponse(
                document_id=existing.id,
                title=existing.title,
                chunks_count=len(existing.chunks),
                status="already_indexed",
            )

        # Création du document
        doc_id = str(uuid.uuid4())
        doc_title = title or pdf_content.metadata.title or file_path.stem
        doc_authors = json.dumps(authors) if authors else pdf_content.metadata.authors

        document = Document(
            id=doc_id,
            title=doc_title,
            authors=doc_authors,
            publication_year=year,
            file_path=str(file_path),
            file_hash=pdf_content.metadata.file_hash,
            page_count=pdf_content.metadata.page_count,
            status="indexing",
        )
        db.add(document)
        db.flush()

        # Découpage en chunks
        chunks = chunker.chunk_text(pdf_content.text, pdf_content.pages)

        if not chunks:
            document.status = "error"
            db.commit()
            raise ValueError("Aucun chunk créé - document vide?")

        # Génération des embeddings
        embedder = get_embedder()
        chunk_texts = [c.text for c in chunks]
        embeddings = embedder.embed_texts(chunk_texts)

        # Préparation pour ChromaDB
        chunk_ids = []
        metadatas = []
        db_chunks = []

        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)

            # Métadonnées pour ChromaDB
            metadatas.append({
                "document_id": doc_id,
                "title": doc_title,
                "authors": doc_authors or "",
                "year": year or 0,
                "page_number": chunk.page_number or 0,
                "chunk_index": chunk.index,
            })

            # Chunk pour SQLite
            db_chunks.append(Chunk(
                id=chunk_id,
                document_id=doc_id,
                chunk_index=chunk.index,
                page_number=chunk.page_number,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                token_count=len(chunk.text.split()),
            ))

        # Ajout à ChromaDB
        retriever = get_retriever()
        retriever.add_chunks(
            chunk_ids=chunk_ids,
            texts=chunk_texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        # Ajout à SQLite
        db.add_all(db_chunks)
        document.status = "indexed"
        document.indexed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Document indexé avec succès: {doc_title} ({len(chunks)} chunks)")

        return IndexResponse(
            document_id=doc_id,
            title=doc_title,
            chunks_count=len(chunks),
            status="indexed",
        )

    def index_folder(
        self,
        db: Session,
        folder_path: str | Path,
    ) -> BatchIndexResponse:
        """
        Indexe tous les PDFs d'un dossier.

        Args:
            db: Session SQLAlchemy.
            folder_path: Chemin vers le dossier.

        Returns:
            BatchIndexResponse avec le résumé de l'indexation.
        """
        folder_path = Path(folder_path)

        if not folder_path.exists():
            raise FileNotFoundError(f"Dossier non trouvé: {folder_path}")

        pdf_files = list(folder_path.glob("*.pdf"))
        logger.info(f"Trouvé {len(pdf_files)} fichiers PDF dans {folder_path}")

        documents = []
        errors = []

        for pdf_file in tqdm(pdf_files, desc="Indexation"):
            try:
                response = self.index_document(db, pdf_file)
                documents.append(response)
            except Exception as e:
                error_msg = f"{pdf_file.name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        return BatchIndexResponse(
            processed=len(documents),
            errors=errors,
            documents=documents,
        )

    def delete_document(self, db: Session, document_id: str) -> bool:
        """
        Supprime un document et ses chunks.

        Args:
            db: Session SQLAlchemy.
            document_id: ID du document.

        Returns:
            True si supprimé, False sinon.
        """
        document = db.query(Document).filter(Document.id == document_id).first()

        if not document:
            return False

        # Suppression de ChromaDB
        retriever = get_retriever()
        retriever.delete_document(document_id)

        # Suppression de SQLite (cascade sur chunks)
        db.delete(document)
        db.commit()

        logger.info(f"Document supprimé: {document.title}")
        return True


# Instance globale
indexing_service = IndexingService()

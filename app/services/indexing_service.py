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
from app.core.metadata_analyzer import metadata_analyzer
from app.core.grobid_client import get_grobid_client
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
        doc_year = year or pdf_content.metadata.year

        # Extraction des métadonnées enrichies (GROBID si disponible)
        doc_abstract = pdf_content.metadata.abstract
        doc_keywords = json.dumps(pdf_content.metadata.keywords) if pdf_content.metadata.keywords else None
        doc_doi = pdf_content.metadata.doi
        doc_journal = pdf_content.metadata.journal
        extraction_method = pdf_content.metadata.extraction_method

        # Calcul du score de qualité des métadonnées
        quality_report = metadata_analyzer.analyze(
            title=doc_title,
            authors=doc_authors,
            year=doc_year,
            abstract=doc_abstract,
            keywords=pdf_content.metadata.keywords,
        )

        document = Document(
            id=doc_id,
            title=doc_title,
            authors=doc_authors,
            publication_year=doc_year,
            file_path=str(file_path),
            file_hash=pdf_content.metadata.file_hash,
            page_count=pdf_content.metadata.page_count,
            abstract=doc_abstract,
            keywords=doc_keywords,
            doi=doc_doi,
            journal=doc_journal,
            extraction_method=extraction_method,
            metadata_quality_score=quality_report.score,
            status="indexing",
        )
        db.add(document)
        db.flush()

        # Découpage en chunks (avec sections si GROBID disponible)
        grobid = get_grobid_client()
        sections_data = None

        if grobid.available:
            logger.info("Extraction des sections avec GROBID...")
            full_doc = grobid.extract_full(file_path)
            if full_doc and full_doc.get("sections"):
                sections_data = full_doc["sections"]
                logger.info(f"GROBID: {len(sections_data)} sections extraites")

        if sections_data:
            # Chunking par sections (préserve la structure)
            chunks = chunker.chunk_sections(sections_data)
        else:
            # Fallback: chunking par taille
            chunks = chunker.chunk_text(pdf_content.text, pdf_content.pages)

        if not chunks:
            document.status = "error"
            db.commit()
            raise ValueError("Aucun chunk créé - document vide?")

        # Préparer les textes enrichis avec métadonnées pour l'embedding
        # Cela améliore la recherche par auteur/titre
        authors_str = ""
        if doc_authors:
            try:
                authors_list = json.loads(doc_authors)
                authors_str = ", ".join(authors_list) if isinstance(authors_list, list) else doc_authors
            except (json.JSONDecodeError, TypeError):
                authors_str = doc_authors

        metadata_prefix = f"Titre: {doc_title}"
        if authors_str:
            metadata_prefix += f" | Auteurs: {authors_str}"
        if doc_year:
            metadata_prefix += f" | Année: {doc_year}"

        # Textes enrichis pour l'embedding (métadonnées + section + contenu)
        chunk_texts_for_embedding = []
        for c in chunks:
            prefix = metadata_prefix
            if c.section:
                section_label = {
                    "introduction": "Introduction",
                    "methods": "Méthodes",
                    "results": "Résultats",
                    "discussion": "Discussion",
                    "conclusion": "Conclusion",
                    "abstract": "Résumé",
                    "references": "Références",
                }.get(c.section, c.section_title or "")
                if section_label:
                    prefix += f" | Section: {section_label}"
            chunk_texts_for_embedding.append(f"{prefix}\n\n{c.text}")
        # Textes originaux pour le stockage
        chunk_texts = [c.text for c in chunks]

        # Génération des embeddings avec textes enrichis
        embedder = get_embedder()
        embeddings = embedder.embed_texts(chunk_texts_for_embedding)

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
                "year": doc_year or 0,
                "page_number": chunk.page_number or 0,
                "chunk_index": chunk.index,
                "doi": doc_doi or "",
                "journal": doc_journal or "",
                "section": chunk.section or "",
                "section_title": chunk.section_title or "",
            })

            # Chunk pour SQLite
            db_chunks.append(Chunk(
                id=chunk_id,
                document_id=doc_id,
                chunk_index=chunk.index,
                page_number=chunk.page_number,
                section_title=chunk.section_title,
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

    def reindex_embeddings(
        self,
        db: Session,
        document_id: str | None = None,
    ) -> dict:
        """
        Réindexe les embeddings d'un ou tous les documents.

        Args:
            db: Session SQLAlchemy.
            document_id: ID du document (optionnel, tous si None).

        Returns:
            Dictionnaire avec le résumé de la réindexation.
        """
        if document_id:
            documents = db.query(Document).filter(
                Document.id == document_id,
                Document.status == "indexed"
            ).all()
        else:
            documents = db.query(Document).filter(Document.status == "indexed").all()

        if not documents:
            return {"reindexed": 0, "errors": [], "message": "Aucun document à réindexer"}

        embedder = get_embedder()
        retriever = get_retriever()
        reindexed = 0
        errors = []

        for document in tqdm(documents, desc="Réindexation embeddings"):
            try:
                # Récupérer les chunks du document
                chunks = db.query(Chunk).filter(Chunk.document_id == document.id).order_by(Chunk.chunk_index).all()

                if not chunks:
                    continue

                # Récupérer les textes depuis ChromaDB
                chunk_ids = [c.id for c in chunks]
                existing_data = retriever.collection.get(ids=chunk_ids, include=["documents", "metadatas"])

                if not existing_data["documents"]:
                    continue

                # Préparer les métadonnées pour l'embedding enrichi
                authors_str = ""
                if document.authors:
                    try:
                        authors_list = json.loads(document.authors)
                        authors_str = ", ".join(authors_list) if isinstance(authors_list, list) else document.authors
                    except (json.JSONDecodeError, TypeError):
                        authors_str = document.authors

                metadata_prefix = f"Titre: {document.title}"
                if authors_str:
                    metadata_prefix += f" | Auteurs: {authors_str}"
                if document.publication_year:
                    metadata_prefix += f" | Année: {document.publication_year}"

                # Textes enrichis pour les nouveaux embeddings
                chunk_texts_for_embedding = [
                    f"{metadata_prefix}\n\n{text}" for text in existing_data["documents"]
                ]

                # Générer les nouveaux embeddings
                new_embeddings = embedder.embed_texts(chunk_texts_for_embedding)

                # Mettre à jour dans ChromaDB
                retriever.collection.update(
                    ids=chunk_ids,
                    embeddings=new_embeddings,
                )

                reindexed += 1
                logger.info(f"Embeddings réindexés pour: {document.title}")

            except Exception as e:
                error_msg = f"{document.title}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        return {
            "reindexed": reindexed,
            "total": len(documents),
            "errors": errors,
            "message": f"{reindexed}/{len(documents)} documents réindexés"
        }

    def reset_all(self, db: Session) -> dict:
        """
        Réinitialise complètement les bases de données.

        Supprime tous les documents de SQLite et tous les chunks de ChromaDB.

        Args:
            db: Session SQLAlchemy.

        Returns:
            Dictionnaire avec le résumé de la réinitialisation.
        """
        # Compter avant suppression
        doc_count = db.query(Document).count()
        chunk_count = db.query(Chunk).count()

        # Supprimer tous les chunks de ChromaDB
        try:
            retriever = get_retriever()
            # Récupérer tous les IDs et les supprimer
            all_data = retriever.collection.get()
            if all_data["ids"]:
                retriever.collection.delete(ids=all_data["ids"])
            logger.info(f"ChromaDB vidé: {len(all_data['ids'])} chunks supprimés")
        except Exception as e:
            logger.error(f"Erreur lors du vidage ChromaDB: {e}")

        # Supprimer tous les documents SQLite (cascade sur chunks)
        db.query(Chunk).delete()
        db.query(Document).delete()
        db.commit()

        logger.info(f"Base réinitialisée: {doc_count} documents, {chunk_count} chunks supprimés")

        return {
            "status": "reset_complete",
            "documents_deleted": doc_count,
            "chunks_deleted": chunk_count,
            "message": f"Base réinitialisée: {doc_count} documents supprimés"
        }

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

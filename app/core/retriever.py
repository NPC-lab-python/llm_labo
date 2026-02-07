"""Recherche sémantique dans la base vectorielle ChromaDB."""

from dataclasses import dataclass

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from config import settings
from app.core.embedder import get_embedder


@dataclass
class RetrievedChunk:
    """Chunk récupéré avec son score de pertinence."""

    chunk_id: str
    document_id: str
    text: str
    title: str
    authors: str | None
    year: int | None
    page_number: int | None
    relevance_score: float
    section: str | None = None
    section_title: str | None = None


class VectorRetriever:
    """Recherche sémantique dans ChromaDB."""

    def __init__(self):
        """Initialise la connexion à ChromaDB."""
        settings.ensure_directories()

        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

        self.embedder = get_embedder()

    def add_chunks(
        self,
        chunk_ids: list[str],
        texts: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict],
    ) -> None:
        """
        Ajoute des chunks à la collection.

        Args:
            chunk_ids: IDs uniques des chunks.
            texts: Textes des chunks.
            embeddings: Vecteurs d'embeddings.
            metadatas: Métadonnées associées.
        """
        logger.info(f"Ajout de {len(chunk_ids)} chunks à ChromaDB")

        self.collection.add(
            ids=chunk_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        logger.info("Chunks ajoutés avec succès")

    def search(
        self,
        query: str,
        top_k: int | None = None,
        filters: dict | None = None,
    ) -> list[RetrievedChunk]:
        """
        Recherche les chunks les plus pertinents.

        Args:
            query: Question de l'utilisateur.
            top_k: Nombre de résultats à retourner.
            filters: Filtres sur les métadonnées (year, authors, section, etc.).

        Returns:
            Liste de RetrievedChunk triés par pertinence.
        """
        top_k = top_k or settings.default_top_k

        logger.info(f"Recherche: '{query[:50]}...' (top_k={top_k})")

        # Génération de l'embedding de la requête
        query_embedding = self.embedder.embed_query(query)

        # Construction des filtres ChromaDB
        where_filter = None
        author_filter = None  # Filtre auteur géré en post-traitement
        if filters:
            where_clauses = []
            if filters.get("year_min"):
                where_clauses.append({"year": {"$gte": filters["year_min"]}})
            if filters.get("year_max"):
                where_clauses.append({"year": {"$lte": filters["year_max"]}})
            if filters.get("section"):
                # Filtre par section en post-traitement
                # car le champ peut ne pas exister dans les anciennes métadonnées
                top_k = top_k * 3
            if filters.get("authors"):
                # ChromaDB ne supporte pas $contains, on filtre en post-traitement
                author_filter = filters["authors"]
                if isinstance(author_filter, list):
                    author_filter = author_filter[0].lower()
                else:
                    author_filter = author_filter.lower()
                # Augmenter top_k pour compenser le filtrage
                top_k = top_k * 5
            if where_clauses:
                where_filter = {"$and": where_clauses} if len(where_clauses) > 1 else where_clauses[0]

        # Vérifier si la collection a des documents
        collection_count = self.collection.count()
        if collection_count == 0:
            logger.warning("Collection ChromaDB vide - aucun document indexé")
            return []

        # Recherche
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection_count),
                where=where_filter,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Erreur ChromaDB lors de la recherche: {e}")
            return []

        # Conversion des résultats
        chunks = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0

                # Conversion distance cosinus en score de similarité
                relevance_score = 1 - distance

                chunks.append(
                    RetrievedChunk(
                        chunk_id=chunk_id,
                        document_id=metadata.get("document_id", ""),
                        text=results["documents"][0][i] if results["documents"] else "",
                        title=metadata.get("title", ""),
                        authors=metadata.get("authors"),
                        year=metadata.get("year"),
                        page_number=metadata.get("page_number"),
                        relevance_score=relevance_score,
                        section=metadata.get("section"),
                        section_title=metadata.get("section_title"),
                    )
                )

        # Post-filtrage par auteur si nécessaire
        if author_filter and chunks:
            chunks = [
                c for c in chunks
                if c.authors and author_filter in c.authors.lower()
            ]
            logger.info(f"Après filtrage par auteur '{author_filter}': {len(chunks)} chunks")

        # Post-filtrage par section si nécessaire
        if filters and filters.get("section") and chunks:
            section_filter = filters["section"].lower()
            chunks = [
                c for c in chunks
                if c.section and c.section.lower() == section_filter
            ]
            logger.info(f"Après filtrage par section '{section_filter}': {len(chunks)} chunks")

        logger.info(f"Trouvé {len(chunks)} chunks pertinents")
        return chunks

    def delete_document(self, document_id: str) -> None:
        """Supprime tous les chunks d'un document."""
        logger.info(f"Suppression des chunks du document {document_id}")

        self.collection.delete(where={"document_id": document_id})

    def get_stats(self) -> dict:
        """Retourne les statistiques de la collection."""
        return {
            "total_chunks": self.collection.count(),
            "collection_name": settings.chroma_collection_name,
        }


# Instance globale (lazy loading)
_retriever: VectorRetriever | None = None


def get_retriever() -> VectorRetriever:
    """Retourne l'instance du retriever (lazy loading)."""
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever


def reset_retriever() -> None:
    """Réinitialise l'instance du retriever (utile après suppression des données)."""
    global _retriever
    _retriever = None
    logger.info("Instance du retriever réinitialisée")

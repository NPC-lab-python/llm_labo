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
            filters: Filtres sur les métadonnées (year, authors, etc.).

        Returns:
            Liste de RetrievedChunk triés par pertinence.
        """
        top_k = top_k or settings.default_top_k

        logger.info(f"Recherche: '{query[:50]}...' (top_k={top_k})")

        # Génération de l'embedding de la requête
        query_embedding = self.embedder.embed_query(query)

        # Construction des filtres ChromaDB
        where_filter = None
        if filters:
            where_clauses = []
            if filters.get("year_min"):
                where_clauses.append({"year": {"$gte": filters["year_min"]}})
            if filters.get("year_max"):
                where_clauses.append({"year": {"$lte": filters["year_max"]}})
            if where_clauses:
                where_filter = {"$and": where_clauses} if len(where_clauses) > 1 else where_clauses[0]

        # Recherche
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

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
                    )
                )

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

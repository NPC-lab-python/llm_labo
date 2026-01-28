"""Service de requête RAG."""

import time

from loguru import logger

from app.core.retriever import get_retriever
from app.core.generator import get_generator
from app.models.schemas import QueryRequest, QueryResponse, Source


class QueryService:
    """Service de requête RAG."""

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Exécute une requête RAG.

        Args:
            request: Requête avec question et filtres.

        Returns:
            QueryResponse avec réponse et sources.
        """
        start_time = time.time()

        logger.info(f"Requête: {request.question[:50]}...")

        # Construction des filtres
        filters = {}
        if request.year_min:
            filters["year_min"] = request.year_min
        if request.year_max:
            filters["year_max"] = request.year_max

        # Recherche sémantique
        retriever = get_retriever()
        chunks = retriever.search(
            query=request.question,
            top_k=request.top_k,
            filters=filters if filters else None,
        )

        # Génération de la réponse
        generator = get_generator()
        answer = generator.generate(
            question=request.question,
            chunks=chunks,
        )

        # Construction des sources
        sources = [
            Source(
                document_id=chunk.document_id,
                title=chunk.title,
                authors=chunk.authors,
                year=chunk.year,
                page=chunk.page_number,
                relevance_score=chunk.relevance_score,
            )
            for chunk in chunks
        ]

        # Déduplication des sources par document
        seen_docs = set()
        unique_sources = []
        for source in sources:
            if source.document_id not in seen_docs:
                seen_docs.add(source.document_id)
                unique_sources.append(source)

        processing_time = int((time.time() - start_time) * 1000)

        logger.info(f"Requête terminée en {processing_time}ms")

        return QueryResponse(
            answer=answer,
            sources=unique_sources,
            processing_time_ms=processing_time,
        )


# Instance globale
query_service = QueryService()

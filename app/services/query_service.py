"""Service de requête RAG."""

import re
import time

from loguru import logger
from sqlalchemy.orm import Session

from app.core.retriever import get_retriever
from app.core.generator import get_generator
from app.core.reranker import get_reranker
from app.models.schemas import QueryRequest, QueryResponse, Source
from app.models.database import Document, SessionLocal


class QueryService:
    """Service de requête RAG."""

    # Mapping des mots-clés de section
    SECTION_KEYWORDS = {
        "methods": ["méthode", "méthodes", "méthodologie", "protocole", "procédure", "matériel", "method", "methodology"],
        "results": ["résultat", "résultats", "findings", "observations", "données", "result", "results"],
        "discussion": ["discussion", "analyse", "interprétation", "analysis"],
        "conclusion": ["conclusion", "conclusions", "perspectives", "summary"],
        "introduction": ["introduction", "contexte", "background", "préambule"],
        "abstract": ["abstract", "résumé"],
    }

    # Mots-clés pour détecter une demande de synthèse/revue de littérature
    SYNTHESIS_KEYWORDS = [
        "synthèse", "synthétise", "revue de littérature", "revue", "résume tous",
        "résumer tous", "tous les articles", "tous les documents", "ensemble des",
        "vue d'ensemble", "overview", "literature review", "état de l'art",
    ]

    # Mots-clés pour détecter une demande de comparaison
    COMPARISON_KEYWORDS = [
        "compare", "comparer", "comparaison", "différences entre", "similitudes entre",
        "versus", "vs", "par rapport à", "en comparaison", "opposer",
    ]

    def _detect_query_type(self, question: str) -> str:
        """
        Détecte le type de requête (standard, synthesis, comparison).

        Args:
            question: Question de l'utilisateur.

        Returns:
            Type de requête: "standard", "synthesis", ou "comparison".
        """
        question_lower = question.lower()

        # Vérifier si c'est une comparaison (prioritaire car plus spécifique)
        for keyword in self.COMPARISON_KEYWORDS:
            if keyword in question_lower:
                logger.info(f"Type de requête détecté: comparison (mot-clé: '{keyword}')")
                return "comparison"

        # Vérifier si c'est une synthèse
        for keyword in self.SYNTHESIS_KEYWORDS:
            if keyword in question_lower:
                logger.info(f"Type de requête détecté: synthesis (mot-clé: '{keyword}')")
                return "synthesis"

        return "standard"

    def _detect_multiple_authors(self, question: str) -> list[str]:
        """
        Détecte plusieurs auteurs mentionnés dans une question de comparaison.

        Args:
            question: Question de l'utilisateur.

        Returns:
            Liste des noms d'auteurs détectés.
        """
        # Patterns pour détecter les comparaisons d'auteurs
        # "compare Jehl et Dupont", "différences entre Martin et Bernard"
        patterns = [
            r"(?:compare|comparer|comparaison|différences entre|similitudes entre)[^A-Z]*([A-Z][a-zàâäéèêëïîôùûüç]+)\s+(?:et|and|vs|versus)\s+([A-Z][a-zàâäéèêëïîôùûüç]+)",
            r"([A-Z][a-zàâäéèêëïîôùûüç]+)\s+(?:et|and|vs|versus)\s+([A-Z][a-zàâäéèêëïîôùûüç]+)",
        ]

        detected_authors = []
        db = SessionLocal()
        try:
            for pattern in patterns:
                matches = re.findall(pattern, question, re.IGNORECASE)
                for match in matches:
                    for name in match:
                        name_clean = name.strip().lower()
                        if len(name_clean) < 3:
                            continue
                        # Vérifier si l'auteur existe en base
                        doc = db.query(Document).filter(
                            Document.authors.ilike(f"%{name_clean}%")
                        ).first()
                        if doc and name_clean not in detected_authors:
                            detected_authors.append(name_clean)
        finally:
            db.close()

        logger.info(f"Auteurs détectés pour comparaison: {detected_authors}")
        return detected_authors

    def _detect_section_in_query(self, question: str) -> str | None:
        """
        Détecte si la question demande une section spécifique.

        Args:
            question: Question de l'utilisateur.

        Returns:
            Nom de la section normalisée ou None.
        """
        question_lower = question.lower()

        for section, keywords in self.SECTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in question_lower:
                    logger.info(f"Section détectée dans la question: '{section}'")
                    return section

        return None

    def _detect_author_in_query(self, question: str) -> str | None:
        """
        Détecte si la question mentionne un auteur présent dans la base.

        Args:
            question: Question de l'utilisateur.

        Returns:
            Nom de l'auteur détecté ou None.
        """
        # Patterns pour détecter les mentions d'auteurs
        patterns = [
            r"(?:de|par|d'|selon|article de|travaux de|étude de|recherche de|thèse de)\s+([A-Z][a-zàâäéèêëïîôùûüç]+(?:\s+(?:et\s+)?[A-Z][a-zàâäéèêëïîôùûüç]+)*)",
            r"([A-Z][a-zàâäéèêëïîôùûüç]+)(?:\s+et\s+al\.?)?",
        ]

        # Extraire les noms potentiels
        potential_names = []
        for pattern in patterns:
            matches = re.findall(pattern, question, re.IGNORECASE)
            potential_names.extend(matches)

        if not potential_names:
            return None

        # Vérifier si un nom correspond à un auteur en base
        db = SessionLocal()
        try:
            for name in potential_names:
                name_clean = name.strip().lower()
                if len(name_clean) < 3:
                    continue

                # Chercher dans les auteurs des documents
                doc = db.query(Document).filter(
                    Document.authors.ilike(f"%{name_clean}%")
                ).first()

                if doc:
                    logger.info(f"Auteur détecté dans la question: '{name_clean}'")
                    return name_clean
        finally:
            db.close()

        return None

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

        # Détecter le type de requête
        query_type = self._detect_query_type(request.question)

        # Construction des filtres de base
        filters = {}
        if request.year_min:
            filters["year_min"] = request.year_min
        if request.year_max:
            filters["year_max"] = request.year_max
        if request.authors:
            filters["authors"] = request.authors

        # Détection automatique de section
        detected_section = self._detect_section_in_query(request.question)
        if detected_section:
            filters["section"] = detected_section
            logger.info(f"Filtre section auto-détecté: {detected_section}")

        retriever = get_retriever()
        generator = get_generator()
        reranker = get_reranker()

        # Traitement selon le type de requête
        if query_type == "comparison":
            # Mode comparaison d'articles
            return self._handle_comparison_query(
                request, retriever, generator, filters, detected_section, start_time
            )
        elif query_type == "synthesis":
            # Mode revue de littérature
            return self._handle_synthesis_query(
                request, retriever, generator, reranker, filters, detected_section, start_time
            )
        else:
            # Mode standard
            return self._handle_standard_query(
                request, retriever, generator, reranker, filters, start_time
            )

    def _handle_standard_query(
        self,
        request: QueryRequest,
        retriever,
        generator,
        reranker,
        filters: dict,
        start_time: float,
    ) -> QueryResponse:
        """Gère une requête standard."""
        # Détection automatique d'auteur si non spécifié
        if not request.authors:
            detected_author = self._detect_author_in_query(request.question)
            if detected_author:
                filters["authors"] = detected_author
                logger.info(f"Filtre auteur auto-détecté: {detected_author}")

        # Recherche sémantique
        initial_top_k = min(request.top_k * 3, 30)
        chunks = retriever.search(
            query=request.question,
            top_k=initial_top_k,
            filters=filters if filters else None,
        )

        # Reranking
        if reranker.enabled and chunks:
            chunks = reranker.rerank(
                query=request.question,
                chunks=chunks,
                top_k=request.top_k,
            )
        else:
            chunks = chunks[:request.top_k]

        # Génération de la réponse
        answer = generator.generate(
            question=request.question,
            chunks=chunks,
        )

        return self._build_response(chunks, answer, start_time)

    def _handle_synthesis_query(
        self,
        request: QueryRequest,
        retriever,
        generator,
        reranker,
        filters: dict,
        section_filter: str | None,
        start_time: float,
    ) -> QueryResponse:
        """Gère une requête de synthèse/revue de littérature."""
        logger.info("Mode SYNTHÈSE activé")

        # Récupérer plus de chunks pour une synthèse complète
        chunks = retriever.search(
            query=request.question,
            top_k=50,  # Plus de résultats pour couvrir plusieurs documents
            filters=filters if filters else None,
        )

        # Reranking pour garder les plus pertinents
        if reranker.enabled and chunks:
            chunks = reranker.rerank(
                query=request.question,
                chunks=chunks,
                top_k=30,  # Garder les 30 meilleurs
            )
        else:
            chunks = chunks[:30]

        # Génération de la synthèse
        answer = generator.synthesize_literature(
            topic=request.question,
            chunks=chunks,
            section_filter=section_filter,
        )

        return self._build_response(chunks, answer, start_time)

    def _handle_comparison_query(
        self,
        request: QueryRequest,
        retriever,
        generator,
        filters: dict,
        section_filter: str | None,
        start_time: float,
    ) -> QueryResponse:
        """Gère une requête de comparaison d'articles."""
        logger.info("Mode COMPARAISON activé")

        # Détecter les auteurs à comparer
        authors = self._detect_multiple_authors(request.question)

        if len(authors) < 2:
            # Pas assez d'auteurs détectés, fallback sur requête standard
            logger.warning("Moins de 2 auteurs détectés, fallback sur mode standard")
            return self._handle_standard_query(
                request, retriever, generator, get_reranker(), filters, start_time
            )

        # Récupérer les chunks pour chaque auteur
        chunks_by_author = {}
        all_chunks = []

        for author in authors:
            author_filters = filters.copy()
            author_filters["authors"] = author

            author_chunks = retriever.search(
                query=request.question,
                top_k=15,
                filters=author_filters,
            )

            if author_chunks:
                chunks_by_author[author] = author_chunks
                all_chunks.extend(author_chunks)

        if not chunks_by_author:
            return QueryResponse(
                answer="Aucun document trouvé pour les auteurs mentionnés.",
                sources=[],
                processing_time_ms=int((time.time() - start_time) * 1000),
            )

        # Génération de la comparaison
        answer = generator.compare_articles(
            authors=authors,
            topic=request.question,
            chunks_by_author=chunks_by_author,
        )

        return self._build_response(all_chunks, answer, start_time)

    def _build_response(
        self,
        chunks: list,
        answer: str,
        start_time: float,
    ) -> QueryResponse:
        """Construit la réponse avec sources dédupliquées."""
        # Construction des sources
        sources = [
            Source(
                document_id=chunk.document_id,
                title=chunk.title,
                authors=chunk.authors,
                year=chunk.year,
                page=chunk.page_number,
                section=chunk.section,
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

"""Reranking des résultats avec un cross-encoder."""

from loguru import logger

try:
    from sentence_transformers import CrossEncoder
    RERANKER_AVAILABLE = True
except ImportError:
    RERANKER_AVAILABLE = False
    logger.warning("sentence-transformers non installé, reranking désactivé")


class Reranker:
    """Reranker basé sur un cross-encoder pour améliorer la pertinence."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialise le reranker.

        Args:
            model_name: Nom du modèle cross-encoder à utiliser.
        """
        self.model_name = model_name
        self.model = None
        self.enabled = RERANKER_AVAILABLE

        if self.enabled:
            try:
                logger.info(f"Chargement du modèle de reranking: {model_name}")
                self.model = CrossEncoder(model_name)
                logger.info("Modèle de reranking chargé")
            except Exception as e:
                logger.error(f"Erreur lors du chargement du reranker: {e}")
                self.enabled = False

    def rerank(
        self,
        query: str,
        chunks: list,
        top_k: int | None = None,
    ) -> list:
        """
        Rerank les chunks en fonction de leur pertinence par rapport à la requête.

        Args:
            query: Question de l'utilisateur.
            chunks: Liste de RetrievedChunk à reranker.
            top_k: Nombre de résultats à retourner (None = tous).

        Returns:
            Liste de chunks rerankés, triés par pertinence.
        """
        if not self.enabled or not chunks:
            return chunks

        logger.info(f"Reranking de {len(chunks)} chunks")

        # Préparer les paires (query, chunk_text)
        pairs = [(query, chunk.text) for chunk in chunks]

        # Calculer les scores de pertinence
        scores = self.model.predict(pairs)

        # Associer les scores aux chunks
        scored_chunks = list(zip(chunks, scores))

        # Trier par score décroissant
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Mettre à jour les scores de pertinence
        reranked_chunks = []
        for chunk, score in scored_chunks:
            # Normaliser le score entre 0 et 1
            chunk.relevance_score = float(score)
            reranked_chunks.append(chunk)

        # Limiter au top_k si spécifié
        if top_k:
            reranked_chunks = reranked_chunks[:top_k]

        logger.info(f"Reranking terminé, top score: {reranked_chunks[0].relevance_score:.3f}")

        return reranked_chunks


# Instance globale (lazy loading)
_reranker: Reranker | None = None


def get_reranker() -> Reranker:
    """Retourne l'instance du reranker (lazy loading)."""
    global _reranker
    if _reranker is None:
        _reranker = Reranker()
    return _reranker

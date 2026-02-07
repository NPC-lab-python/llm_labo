"""Génération d'embeddings avec l'API Voyage AI."""

import time
from loguru import logger
import voyageai

from config import settings


class VoyageEmbedder:
    """Génère des embeddings avec l'API Voyage AI."""

    def __init__(self):
        """Initialise le client Voyage AI."""
        if not settings.voyage_api_key:
            raise ValueError("VOYAGE_API_KEY non configurée")

        self.client = voyageai.Client(api_key=settings.voyage_api_key)
        self.model = settings.voyage_embed_model
        self.batch_size = 128  # Limite Voyage AI
        self.rate_limit_delay = 0.5  # Délai entre les requêtes

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """
        Génère les embeddings pour une liste de textes.

        Args:
            texts: Liste de textes à encoder.

        Returns:
            Liste de vecteurs d'embeddings.
        """
        if not texts:
            return []

        logger.info(f"Génération d'embeddings pour {len(texts)} textes")

        all_embeddings = []

        # Traitement par batch
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            logger.debug(f"Batch {i // self.batch_size + 1}: {len(batch)} textes")

            try:
                response = self.client.embed(
                    texts=batch,
                    model=self.model,
                    input_type="document",
                )

                all_embeddings.extend(response.embeddings)

                # Rate limiting
                if i + self.batch_size < len(texts):
                    time.sleep(self.rate_limit_delay)

            except Exception as e:
                logger.error(f"Erreur lors de la génération d'embeddings: {e}")
                raise

        logger.info(f"Généré {len(all_embeddings)} embeddings")
        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        """
        Génère l'embedding pour une requête.

        Args:
            query: Texte de la requête.

        Returns:
            Vecteur d'embedding.
        """
        try:
            response = self.client.embed(
                texts=[query],
                model=self.model,
                input_type="query",
            )
            return response.embeddings[0]
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'embedding requête: {e}")
            raise


# Instance globale (lazy loading)
_embedder: VoyageEmbedder | None = None


def get_embedder() -> VoyageEmbedder:
    """Retourne l'instance de l'embedder (lazy loading)."""
    global _embedder
    if _embedder is None:
        _embedder = VoyageEmbedder()
    return _embedder

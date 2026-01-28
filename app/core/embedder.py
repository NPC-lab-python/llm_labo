"""Génération d'embeddings avec l'API Mistral."""

import time
from loguru import logger
from mistralai import Mistral

from config import settings


class MistralEmbedder:
    """Génère des embeddings avec l'API Mistral."""

    def __init__(self):
        """Initialise le client Mistral."""
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY non configurée")

        self.client = Mistral(api_key=settings.mistral_api_key)
        self.model = settings.mistral_embed_model
        self.batch_size = 16  # Limite Mistral
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
                response = self.client.embeddings.create(
                    model=self.model,
                    inputs=batch,
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

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
        embeddings = self.embed_texts([query])
        return embeddings[0]


# Instance globale (lazy loading)
_embedder: MistralEmbedder | None = None


def get_embedder() -> MistralEmbedder:
    """Retourne l'instance de l'embedder (lazy loading)."""
    global _embedder
    if _embedder is None:
        _embedder = MistralEmbedder()
    return _embedder

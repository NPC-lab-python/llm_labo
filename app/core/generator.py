"""Génération de réponses avec l'API Mistral."""

from loguru import logger
from mistralai import Mistral

from config import settings
from app.core.retriever import RetrievedChunk


SYSTEM_PROMPT = """Tu es un assistant de recherche académique expert. Tu réponds aux questions en te basant UNIQUEMENT sur les extraits de documents fournis.

Règles importantes:
1. Base tes réponses UNIQUEMENT sur les extraits fournis
2. Cite TOUJOURS tes sources avec le format [Source N]
3. Si l'information n'est pas dans les extraits, dis-le clairement
4. Réponds en français
5. Sois précis et concis
6. Si plusieurs sources disent la même chose, cite-les toutes"""


class ResponseGenerator:
    """Génère des réponses avec Mistral."""

    def __init__(self):
        """Initialise le client Mistral."""
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY non configurée")

        self.client = Mistral(api_key=settings.mistral_api_key)
        self.model = settings.mistral_chat_model

    def generate(
        self,
        question: str,
        chunks: list[RetrievedChunk],
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> str:
        """
        Génère une réponse basée sur les chunks récupérés.

        Args:
            question: Question de l'utilisateur.
            chunks: Chunks pertinents récupérés.
            temperature: Température de génération (0-1).
            max_tokens: Nombre maximum de tokens.

        Returns:
            Réponse générée.
        """
        if not chunks:
            return "Je n'ai pas trouvé d'informations pertinentes dans les documents pour répondre à cette question."

        logger.info(f"Génération de réponse pour: '{question[:50]}...'")

        # Construction du contexte
        context = self._build_context(chunks)

        # Construction du prompt
        user_prompt = f"""Contexte (extraits de documents):

{context}

Question: {question}

Réponds en citant les sources pertinentes avec [Source N]."""

        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            answer = response.choices[0].message.content
            logger.info(f"Réponse générée: {len(answer)} caractères")
            return answer

        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            raise

    def _build_context(self, chunks: list[RetrievedChunk]) -> str:
        """Construit le contexte à partir des chunks."""
        context_parts = []

        for i, chunk in enumerate(chunks, 1):
            # Construction de la référence
            ref_parts = []
            if chunk.authors:
                ref_parts.append(chunk.authors)
            if chunk.year:
                ref_parts.append(f"({chunk.year})")
            if chunk.title:
                ref_parts.append(f'"{chunk.title}"')
            if chunk.page_number:
                ref_parts.append(f"p.{chunk.page_number}")

            reference = " ".join(ref_parts) if ref_parts else "Source inconnue"

            context_parts.append(
                f"[Source {i}: {reference}]\n{chunk.text}"
            )

        return "\n\n---\n\n".join(context_parts)


# Instance globale (lazy loading)
_generator: ResponseGenerator | None = None


def get_generator() -> ResponseGenerator:
    """Retourne l'instance du générateur (lazy loading)."""
    global _generator
    if _generator is None:
        _generator = ResponseGenerator()
    return _generator

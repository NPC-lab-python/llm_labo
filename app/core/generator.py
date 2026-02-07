"""Génération de réponses avec l'API Claude (Anthropic)."""

from loguru import logger
import anthropic

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
    """Génère des réponses avec Claude."""

    def __init__(self):
        """Initialise le client Anthropic."""
        if not settings.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY non configurée")

        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

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
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )

            answer = response.content[0].text
            logger.info(f"Réponse générée: {len(answer)} caractères")
            return answer

        except Exception as e:
            logger.error(f"Erreur lors de la génération: {e}")
            raise

    def summarize(
        self,
        title: str,
        text: str,
        authors: str | None = None,
        year: int | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """
        Génère un résumé d'un document.

        Args:
            title: Titre du document.
            text: Texte du document (ou extrait).
            authors: Auteurs du document.
            year: Année de publication.
            max_tokens: Nombre maximum de tokens.

        Returns:
            Résumé généré.
        """
        logger.info(f"Génération de résumé pour: '{title[:50]}...'")

        # Construction du prompt
        metadata = f"Titre: {title}"
        if authors:
            metadata += f"\nAuteurs: {authors}"
        if year:
            metadata += f"\nAnnée: {year}"

        user_prompt = f"""{metadata}

Texte du document:
{text[:30000]}

---

Génère un résumé structuré de ce document académique en français avec:
1. **Objectif principal** : Quel est le but de cette recherche ?
2. **Méthodologie** : Quelle approche/méthode a été utilisée ?
3. **Résultats clés** : Quelles sont les principales découvertes ?
4. **Conclusions** : Quelles sont les implications et conclusions ?

Sois précis et concis (environ 300-500 mots)."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system="Tu es un assistant expert en analyse de documents académiques. Tu génères des résumés clairs et structurés en français.",
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )

            summary = response.content[0].text
            logger.info(f"Résumé généré: {len(summary)} caractères")
            return summary

        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé: {e}")
            raise

    def synthesize_literature(
        self,
        topic: str,
        chunks: list[RetrievedChunk],
        section_filter: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """
        Génère une synthèse de littérature à partir de plusieurs documents.

        Args:
            topic: Sujet de la synthèse.
            chunks: Chunks de plusieurs documents.
            section_filter: Section spécifique (methods, results, etc.).
            max_tokens: Nombre maximum de tokens.

        Returns:
            Synthèse structurée.
        """
        if not chunks:
            return "Aucun document trouvé pour réaliser cette synthèse."

        logger.info(f"Génération de synthèse sur: '{topic[:50]}...'")

        # Grouper les chunks par document pour la synthèse
        docs_info = {}
        for chunk in chunks:
            doc_id = chunk.document_id
            if doc_id not in docs_info:
                docs_info[doc_id] = {
                    "title": chunk.title,
                    "authors": chunk.authors,
                    "year": chunk.year,
                    "texts": [],
                }
            docs_info[doc_id]["texts"].append(chunk.text)

        # Construction du contexte par document
        context_parts = []
        for i, (doc_id, info) in enumerate(docs_info.items(), 1):
            ref = f"{info['authors'] or 'Auteur inconnu'}"
            if info['year']:
                ref += f" ({info['year']})"
            ref += f" - {info['title']}"

            combined_text = "\n\n".join(info["texts"][:5])  # Limiter à 5 chunks par doc
            context_parts.append(f"[Document {i}: {ref}]\n{combined_text}")

        context = "\n\n===\n\n".join(context_parts)

        section_instruction = ""
        if section_filter:
            section_labels = {
                "methods": "les méthodes/méthodologies",
                "results": "les résultats",
                "discussion": "les discussions",
                "conclusion": "les conclusions",
                "introduction": "les introductions/contextes",
            }
            section_instruction = f"\nConcentre-toi particulièrement sur {section_labels.get(section_filter, section_filter)}."

        user_prompt = f"""Voici des extraits de {len(docs_info)} documents académiques sur le sujet: "{topic}"
{section_instruction}

{context}

---

Génère une **revue de littérature structurée** en français qui:
1. **Vue d'ensemble** : Présente le thème général et son importance
2. **Synthèse thématique** : Regroupe les approches similaires et identifie les tendances
3. **Points de convergence** : Ce sur quoi les auteurs s'accordent
4. **Points de divergence** : Les différences d'approches ou de résultats
5. **Lacunes identifiées** : Ce qui manque dans la littérature actuelle

Cite chaque document avec [Document N] quand tu y fais référence.
Sois exhaustif mais concis (500-800 mots)."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system="Tu es un expert en synthèse de littérature académique. Tu analyses et synthétises des travaux de recherche de manière objective et structurée en français.",
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )

            synthesis = response.content[0].text
            logger.info(f"Synthèse générée: {len(synthesis)} caractères, {len(docs_info)} documents")
            return synthesis

        except Exception as e:
            logger.error(f"Erreur lors de la synthèse: {e}")
            raise

    def compare_articles(
        self,
        authors: list[str],
        topic: str,
        chunks_by_author: dict[str, list[RetrievedChunk]],
        max_tokens: int = 2048,
    ) -> str:
        """
        Génère une comparaison entre les travaux de plusieurs auteurs.

        Args:
            authors: Liste des noms d'auteurs à comparer.
            topic: Sujet/aspect à comparer.
            chunks_by_author: Dictionnaire {auteur: [chunks]}.
            max_tokens: Nombre maximum de tokens.

        Returns:
            Analyse comparative structurée.
        """
        if not chunks_by_author:
            return "Aucun document trouvé pour ces auteurs."

        logger.info(f"Génération de comparaison entre: {', '.join(authors)}")

        # Construction du contexte par auteur
        context_parts = []
        for author, chunks in chunks_by_author.items():
            if not chunks:
                continue

            # Info du premier chunk pour les métadonnées
            first_chunk = chunks[0]
            ref = f"{first_chunk.authors or author}"
            if first_chunk.year:
                ref += f" ({first_chunk.year})"
            ref += f" - {first_chunk.title}"

            combined_text = "\n\n".join([c.text for c in chunks[:5]])
            context_parts.append(f"### {author.upper()}\n[{ref}]\n\n{combined_text}")

        context = "\n\n===\n\n".join(context_parts)

        user_prompt = f"""Compare les travaux des auteurs suivants concernant: "{topic}"

{context}

---

Génère une **analyse comparative structurée** en français avec:

1. **Tableau comparatif** : Résume les caractéristiques principales de chaque approche
2. **Méthodologies** : Compare les méthodes utilisées par chaque auteur
3. **Résultats** : Compare les résultats/conclusions de chaque étude
4. **Similitudes** : Points communs entre les travaux
5. **Différences** : Divergences significatives
6. **Complémentarité** : Comment ces travaux se complètent-ils ?

Sois objectif et précis. Cite les auteurs quand tu fais référence à leurs travaux.
(400-600 mots)"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system="Tu es un expert en analyse comparative de littérature académique. Tu compares objectivement les travaux de différents chercheurs en français.",
                messages=[
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )

            comparison = response.content[0].text
            logger.info(f"Comparaison générée: {len(comparison)} caractères")
            return comparison

        except Exception as e:
            logger.error(f"Erreur lors de la comparaison: {e}")
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

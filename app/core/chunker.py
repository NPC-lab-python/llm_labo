"""Découpage du texte en chunks pour l'indexation."""

import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from config import settings


# Mapping des titres de section vers des noms normalisés
SECTION_MAPPING = {
    # Introduction
    "introduction": "introduction",
    "contexte": "introduction",
    "background": "introduction",
    "préambule": "introduction",
    # Méthodes
    "method": "methods",
    "methods": "methods",
    "methodology": "methods",
    "méthodologie": "methods",
    "méthodes": "methods",
    "materials and methods": "methods",
    "matériel et méthodes": "methods",
    "experimental": "methods",
    "experimental setup": "methods",
    "protocole": "methods",
    # Résultats
    "result": "results",
    "results": "results",
    "résultats": "results",
    "findings": "results",
    "observations": "results",
    # Discussion
    "discussion": "discussion",
    "analyse": "discussion",
    "analysis": "discussion",
    "interprétation": "discussion",
    # Conclusion
    "conclusion": "conclusion",
    "conclusions": "conclusion",
    "summary": "conclusion",
    "résumé": "conclusion",
    "perspectives": "conclusion",
    # Abstract
    "abstract": "abstract",
    "résumé": "abstract",
    # Références
    "references": "references",
    "références": "references",
    "bibliography": "references",
    "bibliographie": "references",
}


def normalize_section(title: str) -> str:
    """Normalise un titre de section."""
    if not title:
        return "other"

    title_lower = title.lower().strip()

    # Supprimer les numéros de section (1., 2., I., II., etc.)
    title_lower = re.sub(r"^[\d\.\s]+|^[ivxlc]+[\.\s]+", "", title_lower, flags=re.IGNORECASE)
    title_lower = title_lower.strip()

    # Chercher une correspondance
    for key, normalized in SECTION_MAPPING.items():
        if key in title_lower:
            return normalized

    return "other"


@dataclass
class Chunk:
    """Un chunk de texte avec ses métadonnées."""

    text: str
    index: int
    page_number: int | None
    char_start: int
    char_end: int
    section: str | None = None  # Section normalisée (introduction, methods, results, etc.)
    section_title: str | None = None  # Titre original de la section


class TextChunker:
    """Découpe le texte en chunks optimisés pour le RAG."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        """
        Initialise le chunker.

        Args:
            chunk_size: Taille maximale d'un chunk en caractères.
            chunk_overlap: Chevauchement entre les chunks.
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def chunk_text(self, text: str, pages: list[str] | None = None) -> list[Chunk]:
        """
        Découpe le texte en chunks.

        Args:
            text: Texte complet à découper.
            pages: Liste du texte par page (optionnel, pour tracking des pages).

        Returns:
            Liste de Chunk avec métadonnées.
        """
        logger.info(f"Découpage de {len(text)} caractères en chunks")

        # Découpage avec LangChain
        raw_chunks = self.splitter.split_text(text)

        chunks = []
        current_pos = 0

        for idx, chunk_text in enumerate(raw_chunks):
            # Trouver la position dans le texte original
            char_start = text.find(chunk_text, current_pos)
            if char_start == -1:
                char_start = current_pos
            char_end = char_start + len(chunk_text)
            current_pos = char_start + 1

            # Déterminer le numéro de page
            page_number = None
            if pages:
                page_number = self._find_page_number(char_start, text, pages)

            chunks.append(
                Chunk(
                    text=chunk_text,
                    index=idx,
                    page_number=page_number,
                    char_start=char_start,
                    char_end=char_end,
                )
            )

        logger.info(f"Créé {len(chunks)} chunks")
        return chunks

    def _find_page_number(
        self,
        char_pos: int,
        full_text: str,
        pages: list[str],
    ) -> int | None:
        """Trouve le numéro de page correspondant à une position."""
        page_markers = list(re.finditer(r"\[Page (\d+)\]", full_text[:char_pos]))
        if page_markers:
            last_marker = page_markers[-1]
            return int(last_marker.group(1))
        return 1  # Par défaut, page 1

    def chunk_sections(self, sections: list[dict]) -> list[Chunk]:
        """
        Découpe les sections extraites par GROBID en chunks.

        Chaque chunk conserve l'information de sa section d'origine.

        Args:
            sections: Liste de dict avec 'title' et 'text' (depuis GROBID).

        Returns:
            Liste de Chunk avec métadonnées de section.
        """
        if not sections:
            logger.warning("Aucune section fournie pour le chunking")
            return []

        logger.info(f"Découpage de {len(sections)} sections en chunks")

        all_chunks = []
        global_index = 0

        for section in sections:
            section_title = section.get("title", "")
            section_text = section.get("text", "")

            if not section_text.strip():
                continue

            # Normaliser le nom de la section
            normalized_section = normalize_section(section_title)

            # Découper le texte de la section
            raw_chunks = self.splitter.split_text(section_text)

            for chunk_text in raw_chunks:
                # Trouver la position dans le texte de la section
                char_start = section_text.find(chunk_text)
                char_end = char_start + len(chunk_text) if char_start != -1 else len(chunk_text)

                all_chunks.append(
                    Chunk(
                        text=chunk_text,
                        index=global_index,
                        page_number=None,  # Non disponible avec GROBID sections
                        char_start=char_start if char_start != -1 else 0,
                        char_end=char_end,
                        section=normalized_section,
                        section_title=section_title,
                    )
                )
                global_index += 1

        logger.info(f"Créé {len(all_chunks)} chunks à partir des sections")

        # Log des sections trouvées
        section_counts = {}
        for chunk in all_chunks:
            section_counts[chunk.section] = section_counts.get(chunk.section, 0) + 1
        logger.info(f"Distribution des sections: {section_counts}")

        return all_chunks


# Instance globale
chunker = TextChunker()

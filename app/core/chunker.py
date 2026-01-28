"""Découpage du texte en chunks pour l'indexation."""

from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from config import settings


@dataclass
class Chunk:
    """Un chunk de texte avec ses métadonnées."""

    text: str
    index: int
    page_number: int | None
    char_start: int
    char_end: int


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
        # Recherche du marqueur [Page X] avant la position
        import re

        page_markers = list(re.finditer(r"\[Page (\d+)\]", full_text[:char_pos]))
        if page_markers:
            last_marker = page_markers[-1]
            return int(last_marker.group(1))
        return 1  # Par défaut, page 1


# Instance globale
chunker = TextChunker()

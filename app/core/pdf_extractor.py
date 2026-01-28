"""Extraction de texte et métadonnées depuis les fichiers PDF."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF
from loguru import logger


@dataclass
class PDFMetadata:
    """Métadonnées extraites d'un PDF."""

    title: str | None
    authors: str | None
    creation_date: str | None
    page_count: int
    file_hash: str


@dataclass
class PDFContent:
    """Contenu extrait d'un PDF."""

    text: str
    metadata: PDFMetadata
    pages: list[str]


class PDFExtractor:
    """Extracteur de texte et métadonnées PDF."""

    def extract(self, file_path: Path | str) -> PDFContent:
        """
        Extrait le texte et les métadonnées d'un fichier PDF.

        Args:
            file_path: Chemin vers le fichier PDF.

        Returns:
            PDFContent avec le texte et les métadonnées.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            ValueError: Si le fichier n'est pas un PDF valide.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

        if file_path.suffix.lower() != ".pdf":
            raise ValueError(f"Le fichier n'est pas un PDF: {file_path}")

        logger.info(f"Extraction du PDF: {file_path.name}")

        # Calcul du hash pour déduplication
        file_hash = self._compute_hash(file_path)

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Impossible d'ouvrir le PDF: {e}")

        try:
            # Extraction des métadonnées
            metadata = self._extract_metadata(doc, file_hash)

            # Extraction du texte page par page
            pages = []
            full_text_parts = []

            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                pages.append(page_text)
                full_text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

            full_text = "\n\n".join(full_text_parts)

            logger.info(
                f"Extraction terminée: {metadata.page_count} pages, "
                f"{len(full_text)} caractères"
            )

            return PDFContent(
                text=full_text,
                metadata=metadata,
                pages=pages,
            )

        finally:
            doc.close()

    def _extract_metadata(self, doc: fitz.Document, file_hash: str) -> PDFMetadata:
        """Extrait les métadonnées du document."""
        meta = doc.metadata

        # Essayer d'extraire le titre
        title = meta.get("title")
        if not title or title.strip() == "":
            # Essayer de récupérer le titre depuis la première page
            if doc.page_count > 0:
                first_page_text = doc[0].get_text("text")
                lines = [l.strip() for l in first_page_text.split("\n") if l.strip()]
                if lines:
                    title = lines[0][:200]  # Limiter la longueur

        # Auteurs
        authors = meta.get("author")

        # Date de création
        creation_date = meta.get("creationDate")

        return PDFMetadata(
            title=title,
            authors=authors,
            creation_date=creation_date,
            page_count=doc.page_count,
            file_hash=file_hash,
        )

    def _compute_hash(self, file_path: Path) -> str:
        """Calcule le hash SHA256 du fichier."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# Instance globale
pdf_extractor = PDFExtractor()

"""Extraction de texte et métadonnées depuis les fichiers PDF."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
from loguru import logger

from config import settings
from app.core.grobid_client import get_grobid_client, GrobidMetadata


@dataclass
class PDFMetadata:
    """Métadonnées extraites d'un PDF."""

    title: str | None
    authors: str | None
    year: int | None
    creation_date: str | None
    page_count: int
    file_hash: str
    abstract: str | None = None
    keywords: list[str] | None = None
    doi: str | None = None
    journal: str | None = None
    extraction_method: str = "pymupdf"  # "pymupdf" ou "grobid"


@dataclass
class PDFContent:
    """Contenu extrait d'un PDF."""

    text: str
    metadata: PDFMetadata
    pages: list[str]


class PDFExtractor:
    """Extracteur de texte et métadonnées PDF avec extraction intelligente."""

    def __init__(self, grobid_url: str | None = None, use_grobid: bool = True):
        """
        Initialise l'extracteur PDF.

        Args:
            grobid_url: URL du serveur GROBID (optionnel).
            use_grobid: Active l'extraction GROBID si disponible.
        """
        self.use_grobid = use_grobid
        self._grobid_client = None
        self._grobid_url = grobid_url

        if use_grobid:
            self._grobid_client = get_grobid_client(grobid_url)
            if self._grobid_client.available:
                logger.info("GROBID disponible - extraction enrichie activée")
            else:
                logger.info("GROBID non disponible - extraction PyMuPDF uniquement")

    # Patterns à ignorer pour les titres (DOI, URLs, arXiv, etc.)
    INVALID_TITLE_PATTERNS = [
        r"^doi:",
        r"^https?://",
        r"^www\.",
        r"^arXiv:",
        r"^\d+:\d+",  # Format "123:456"
        r"^See discussions",
        r"^Online Submissions",
        r"^Downloaded from",
        r"^\d{1,2}/\d{1,2}/\d{2,4}",  # Dates
        r"^Page \d+",
        r"^©",
        r"^Copyright",
        r"^All rights reserved",
        r"^ISSN",
        r"^ISBN",
        r"\.pdf$",
    ]

    # Patterns pour extraire l'année
    YEAR_PATTERNS = [
        r"(?:published|received|accepted|submitted)[:\s]+(?:\w+\s+)?(\d{4})",
        r"(?:©|copyright)\s*(\d{4})",
        r"\b(19[89]\d|20[0-2]\d)\b",  # Années 1980-2029
    ]

    # Patterns pour détecter les auteurs
    AUTHOR_PATTERNS = [
        # Nom avec initiales: "J. Smith", "Jean-Pierre Dupont"
        r"([A-Z][a-zéèêëàâäùûüîïôö\-\']+(?:\s+[A-Z]\.?\s*)?[A-Z][a-zéèêëàâäùûüîïôö\-\']+)",
        # Noms séparés par virgules ou "and"
        r"([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+\s+[A-Z][a-z]+)*(?:\s+and\s+[A-Z][a-z]+\s+[A-Z][a-z]+)?)",
    ]

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

        logger.debug(f"Extraction du PDF: {file_path.name}")

        # Calcul du hash pour déduplication
        file_hash = self._compute_hash(file_path)

        try:
            doc = fitz.open(file_path)
        except Exception as e:
            raise ValueError(f"Impossible d'ouvrir le PDF: {e}")

        try:
            # Extraction du texte page par page
            pages = []
            full_text_parts = []

            for page_num, page in enumerate(doc):
                page_text = page.get_text("text")
                pages.append(page_text)
                full_text_parts.append(f"[Page {page_num + 1}]\n{page_text}")

            full_text = "\n\n".join(full_text_parts)

            # Extraction des métadonnées avec analyse du contenu
            metadata = self._extract_metadata(doc, file_hash, file_path, pages)

            logger.debug(
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

    def _extract_metadata(
        self,
        doc: fitz.Document,
        file_hash: str,
        file_path: Path,
        pages: list[str],
    ) -> PDFMetadata:
        """Extrait les métadonnées avec analyse intelligente du contenu."""
        meta = doc.metadata
        first_page_text = pages[0] if pages else ""
        creation_date = meta.get("creationDate")

        # === Essayer GROBID d'abord si disponible ===
        grobid_meta = None
        if self.use_grobid and self._grobid_client and self._grobid_client.available:
            logger.debug(f"Tentative d'extraction GROBID pour {file_path.name}")
            grobid_meta = self._grobid_client.extract_header(file_path)
            if grobid_meta:
                logger.debug(f"GROBID extraction réussie pour {file_path.name}")

        # === Extraction PyMuPDF (fallback ou complément) ===
        pymupdf_title = self._extract_title(doc, meta, first_page_text, file_path)
        pymupdf_authors = self._extract_authors(meta, first_page_text)
        pymupdf_year = self._extract_year(meta, first_page_text)

        # === Fusion des résultats (GROBID prioritaire) ===
        if grobid_meta:
            # Formater les auteurs GROBID
            grobid_authors = None
            if grobid_meta.authors:
                author_names = [a["name"] for a in grobid_meta.authors if a.get("name")]
                if author_names:
                    grobid_authors = ", ".join(author_names)

            # Formater les mots-clés
            keywords = grobid_meta.keywords if grobid_meta.keywords else None

            return PDFMetadata(
                title=grobid_meta.title or pymupdf_title,
                authors=grobid_authors or pymupdf_authors,
                year=grobid_meta.year or pymupdf_year,
                creation_date=creation_date,
                page_count=doc.page_count,
                file_hash=file_hash,
                abstract=grobid_meta.abstract,
                keywords=keywords,
                doi=grobid_meta.doi,
                journal=grobid_meta.journal,
                extraction_method="grobid",
            )

        # === Fallback PyMuPDF uniquement ===
        return PDFMetadata(
            title=pymupdf_title,
            authors=pymupdf_authors,
            year=pymupdf_year,
            creation_date=creation_date,
            page_count=doc.page_count,
            file_hash=file_hash,
            extraction_method="pymupdf",
        )

    def _extract_title(
        self,
        doc: fitz.Document,
        meta: dict,
        first_page_text: str,
        file_path: Path,
    ) -> str:
        """Extrait le titre du document de manière intelligente."""
        # 1. Essayer les métadonnées PDF
        title = meta.get("title", "").strip()
        if title and self._is_valid_title(title):
            return title

        # 2. Analyser la première page avec les tailles de police
        title_from_font = self._extract_title_by_font_size(doc)
        if title_from_font and self._is_valid_title(title_from_font):
            return title_from_font

        # 3. Analyser les premières lignes de texte
        lines = [l.strip() for l in first_page_text.split("\n") if l.strip()]

        for line in lines[:15]:  # Analyser les 15 premières lignes
            # Ignorer les lignes trop courtes ou trop longues
            if len(line) < 10 or len(line) > 300:
                continue

            # Vérifier si c'est un titre valide
            if self._is_valid_title(line):
                # Préférer les lignes qui ressemblent à des titres
                # (commencent par majuscule, pas de caractères spéciaux au début)
                if re.match(r"^[A-Z][A-Za-z]", line):
                    return line[:200]

        # 4. Fallback: prendre la première ligne valide
        for line in lines[:10]:
            if len(line) >= 10 and self._is_valid_title(line):
                return line[:200]

        # 5. Dernier recours: nom du fichier
        return file_path.stem

    def _extract_title_by_font_size(self, doc: fitz.Document) -> str | None:
        """Extrait le titre en analysant les tailles de police."""
        if doc.page_count == 0:
            return None

        try:
            page = doc[0]
            blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

            # Collecter tous les spans avec leur taille de police
            text_spans = []
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and len(text) > 5:
                            text_spans.append({
                                "text": text,
                                "size": span["size"],
                                "y": span["bbox"][1],  # Position verticale
                            })

            if not text_spans:
                return None

            # Trouver la plus grande taille de police dans le tiers supérieur
            max_y = page.rect.height / 3
            top_spans = [s for s in text_spans if s["y"] < max_y]

            if not top_spans:
                return None

            # Trouver le texte avec la plus grande police
            max_size = max(s["size"] for s in top_spans)
            largest_spans = [s for s in top_spans if s["size"] >= max_size * 0.9]

            # Combiner les spans consécutifs de même taille
            if largest_spans:
                title_parts = [s["text"] for s in sorted(largest_spans, key=lambda x: x["y"])]
                title = " ".join(title_parts)
                if self._is_valid_title(title):
                    return title[:200]

        except Exception as e:
            logger.debug(f"Erreur extraction titre par police: {e}")

        return None

    def _is_valid_title(self, text: str) -> bool:
        """Vérifie si le texte ressemble à un titre valide."""
        if not text or len(text) < 5:
            return False

        text_lower = text.lower()

        # Vérifier les patterns invalides
        for pattern in self.INVALID_TITLE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return False

        # Rejeter si c'est principalement des chiffres
        digits = sum(c.isdigit() for c in text)
        if digits > len(text) * 0.5:
            return False

        # Rejeter si trop de caractères spéciaux
        special = sum(not c.isalnum() and not c.isspace() for c in text)
        if special > len(text) * 0.3:
            return False

        return True

    def _extract_authors(self, meta: dict, first_page_text: str) -> str | None:
        """Extrait les auteurs du document."""
        # 1. Essayer les métadonnées PDF
        authors = meta.get("author", "").strip()
        if authors and len(authors) > 2:
            return authors

        # 2. Analyser la première page
        lines = first_page_text.split("\n")

        # Chercher dans les 20 premières lignes (après le titre probable)
        for i, line in enumerate(lines[1:25]):
            line = line.strip()
            if not line or len(line) < 5:
                continue

            # Ignorer les lignes qui sont probablement des affiliations
            if any(kw in line.lower() for kw in ["university", "institute", "department", "laboratory", "lab.", "école", "université"]):
                continue

            # Pattern: plusieurs noms séparés par virgules
            # Ex: "John Smith, Jane Doe, Bob Wilson"
            if re.match(r"^[A-Z][a-zéèêëàâäùûüîïôö\-\']+\s+[A-Z]", line):
                # Vérifier que ça ressemble à une liste de noms
                parts = re.split(r"\s*[,;]\s*|\s+and\s+|\s+et\s+", line)
                valid_names = []
                for part in parts:
                    part = part.strip()
                    # Un nom valide: "Prénom Nom" ou "P. Nom" ou "Prénom P. Nom"
                    if re.match(r"^[A-Z][a-zéèêëàâäùûüîïôö\.\-\']*\s+[A-Z][a-zéèêëàâäùûüîïôö\-\']+", part):
                        valid_names.append(part)
                    elif re.match(r"^[A-Z]\.\s*[A-Z][a-zéèêëàâäùûüîïôö\-\']+", part):
                        valid_names.append(part)

                if len(valid_names) >= 1:
                    # Vérifier que ce n'est pas un titre déguisé
                    if not any(kw in line.lower() for kw in ["the ", "a ", "an ", "study", "analysis", "review"]):
                        return ", ".join(valid_names)

            # Pattern: emails souvent près des auteurs
            if "@" in line and i > 0:
                # La ligne précédente pourrait être les auteurs
                prev_line = lines[i].strip() if i < len(lines) else ""
                if prev_line and re.match(r"^[A-Z]", prev_line):
                    names = re.findall(r"[A-Z][a-zéèêëàâäùûüîïôö\-\']+\s+[A-Z][a-zéèêëàâäùûüîïôö\-\']+", prev_line)
                    if names:
                        return ", ".join(names)

        # 3. Chercher des patterns d'auteurs dans le texte
        author_section = "\n".join(lines[:30])

        # Pattern spécifique pour les articles scientifiques
        # Chercher après "by" ou avant les affiliations
        by_match = re.search(r"(?:^|\n)\s*(?:by|par)\s+([A-Z][^\n]+)", author_section, re.IGNORECASE)
        if by_match:
            potential_authors = by_match.group(1).strip()
            if len(potential_authors) < 200:
                return potential_authors

        return None

    def _extract_year(self, meta: dict, first_page_text: str) -> int | None:
        """Extrait l'année de publication."""
        current_year = datetime.now().year
        candidates = []

        # 1. Depuis la date de création du PDF
        creation_date = meta.get("creationDate", "")
        if creation_date:
            match = re.search(r"D:(\d{4})", creation_date)
            if match:
                year = int(match.group(1))
                if 1950 <= year <= current_year:
                    candidates.append((year, 1))  # Priorité basse

        # 2. Depuis les métadonnées "modDate"
        mod_date = meta.get("modDate", "")
        if mod_date:
            match = re.search(r"D:(\d{4})", mod_date)
            if match:
                year = int(match.group(1))
                if 1950 <= year <= current_year:
                    candidates.append((year, 1))

        # 3. Chercher dans le texte de la première page
        text_lower = first_page_text.lower()

        # Pattern: "Published: 2023" ou "Received: January 2023"
        for pattern in [
            r"(?:published|received|accepted|submitted|revised)[:\s]+(?:\w+\s+)?(\d{4})",
            r"(?:©|copyright|\(c\))\s*(\d{4})",
            r"(\d{4})\s*(?:©|copyright)",
        ]:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                year = int(match)
                if 1950 <= year <= current_year:
                    candidates.append((year, 3))  # Priorité haute

        # Pattern: DOI avec année
        doi_match = re.search(r"doi[:/]\s*10\.\d+/[^\s]+\.(\d{4})", text_lower)
        if doi_match:
            year = int(doi_match.group(1))
            if 1950 <= year <= current_year:
                candidates.append((year, 2))

        # Pattern: arXiv avec année
        arxiv_match = re.search(r"arxiv[:/]\s*(\d{2})(\d{2})\.", text_lower)
        if arxiv_match:
            year_short = int(arxiv_match.group(1))
            year = 2000 + year_short if year_short < 50 else 1900 + year_short
            if 1990 <= year <= current_year:
                candidates.append((year, 2))

        # Pattern: Année dans le contexte journal/volume
        vol_match = re.search(r"(?:vol\.?|volume)\s*\d+[,\s]+(?:no\.?\s*\d+[,\s]+)?(\d{4})", text_lower)
        if vol_match:
            year = int(vol_match.group(1))
            if 1950 <= year <= current_year:
                candidates.append((year, 2))

        # 4. Chercher des années isolées dans les premières lignes (moins fiable)
        for line in first_page_text.split("\n")[:20]:
            matches = re.findall(r"\b(19[89]\d|20[0-2]\d)\b", line)
            for match in matches:
                year = int(match)
                if 1980 <= year <= current_year:
                    candidates.append((year, 0))  # Priorité très basse

        # Sélectionner la meilleure année
        if candidates:
            # Trier par priorité décroissante, puis par année décroissante
            candidates.sort(key=lambda x: (x[1], x[0]), reverse=True)
            return candidates[0][0]

        return None

    def _compute_hash(self, file_path: Path) -> str:
        """Calcule le hash SHA256 du fichier."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


# Instance globale (lazy loading)
_pdf_extractor: PDFExtractor | None = None


def get_pdf_extractor(
    grobid_url: str | None = None,
    use_grobid: bool | None = None,
) -> PDFExtractor:
    """
    Retourne l'instance de l'extracteur PDF (lazy loading).

    Args:
        grobid_url: URL du serveur GROBID (défaut depuis settings).
        use_grobid: Active l'extraction GROBID (défaut depuis settings).

    Returns:
        Instance de PDFExtractor.
    """
    global _pdf_extractor
    if _pdf_extractor is None:
        url = grobid_url or settings.grobid_url
        use = use_grobid if use_grobid is not None else settings.use_grobid
        _pdf_extractor = PDFExtractor(grobid_url=url, use_grobid=use)
    return _pdf_extractor


# Alias pour compatibilité (utilise les settings)
pdf_extractor = PDFExtractor(
    grobid_url=settings.grobid_url,
    use_grobid=settings.use_grobid,
)

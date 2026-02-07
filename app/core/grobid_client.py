"""Client pour l'extraction de métadonnées via GROBID."""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

import requests
from loguru import logger


@dataclass
class GrobidMetadata:
    """Métadonnées extraites par GROBID."""

    title: str | None = None
    authors: list[dict] = field(default_factory=list)  # [{name, affiliation, email}]
    abstract: str | None = None
    keywords: list[str] = field(default_factory=list)
    doi: str | None = None
    year: int | None = None
    journal: str | None = None
    volume: str | None = None
    pages: str | None = None
    publisher: str | None = None
    raw_affiliations: list[str] = field(default_factory=list)


@dataclass
class GrobidReference:
    """Référence bibliographique extraite par GROBID."""

    title: str | None = None
    authors: list[str] = field(default_factory=list)
    year: int | None = None
    journal: str | None = None
    volume: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    publisher: str | None = None
    index: int = 0

    def to_bibtex(self, cite_key: str | None = None) -> str:
        """
        Génère une entrée BibTeX pour cette référence.

        Args:
            cite_key: Clé de citation (générée si non fournie).

        Returns:
            Entrée BibTeX formatée.
        """
        # Générer une clé de citation
        if not cite_key:
            first_author = self.authors[0].split()[-1] if self.authors else "Unknown"
            year_str = str(self.year) if self.year else "nd"
            cite_key = f"{first_author}{year_str}"

        # Déterminer le type d'entrée
        entry_type = "article" if self.journal else "misc"

        lines = [f"@{entry_type}{{{cite_key},"]

        if self.title:
            lines.append(f'  title = {{{self.title}}},')
        if self.authors:
            authors_str = " and ".join(self.authors)
            lines.append(f'  author = {{{authors_str}}},')
        if self.year:
            lines.append(f'  year = {{{self.year}}},')
        if self.journal:
            lines.append(f'  journal = {{{self.journal}}},')
        if self.volume:
            lines.append(f'  volume = {{{self.volume}}},')
        if self.pages:
            lines.append(f'  pages = {{{self.pages}}},')
        if self.doi:
            lines.append(f'  doi = {{{self.doi}}},')
        if self.url:
            lines.append(f'  url = {{{self.url}}},')
        if self.publisher:
            lines.append(f'  publisher = {{{self.publisher}}},')

        lines.append("}")

        return "\n".join(lines)


class GrobidClient:
    """Client pour communiquer avec le serveur GROBID."""

    # Namespace TEI utilisé par GROBID
    TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

    def __init__(self, grobid_url: str = "http://localhost:8070"):
        """
        Initialise le client GROBID.

        Args:
            grobid_url: URL du serveur GROBID.
        """
        self.grobid_url = grobid_url.rstrip("/")
        self._available = None

    @property
    def available(self) -> bool:
        """Vérifie si le serveur GROBID est disponible."""
        if self._available is None:
            self._available = self._check_availability()
        return self._available

    def _check_availability(self) -> bool:
        """Vérifie la disponibilité du serveur GROBID."""
        try:
            response = requests.get(f"{self.grobid_url}/api/isalive", timeout=5)
            if response.status_code == 200:
                logger.info(f"GROBID disponible à {self.grobid_url}")
                return True
        except requests.RequestException:
            pass
        logger.warning(f"GROBID non disponible à {self.grobid_url}")
        return False

    def extract_header(self, pdf_path: Path | str) -> GrobidMetadata | None:
        """
        Extrait les métadonnées de l'en-tête d'un PDF.

        Args:
            pdf_path: Chemin vers le fichier PDF.

        Returns:
            GrobidMetadata ou None si l'extraction échoue.
        """
        if not self.available:
            return None

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            logger.error(f"Fichier non trouvé: {pdf_path}")
            return None

        try:
            with open(pdf_path, "rb") as f:
                response = requests.post(
                    f"{self.grobid_url}/api/processHeaderDocument",
                    files={"input": (pdf_path.name, f, "application/pdf")},
                    data={"consolidateHeader": "1"},  # Enrichir via CrossRef
                    headers={"Accept": "application/xml"},
                    timeout=60,
                )

            if response.status_code != 200:
                logger.warning(f"GROBID erreur {response.status_code}: {pdf_path.name} - {response.text[:200]}")
                return None

            # Vérifier que la réponse est du XML valide
            if not response.text or not response.text.strip().startswith('<?xml'):
                logger.warning(f"GROBID réponse non-XML pour {pdf_path.name}: {response.text[:200]}")
                return None

            return self._parse_tei_header(response.text)

        except requests.RequestException as e:
            logger.error(f"Erreur GROBID pour {pdf_path.name}: {e}")
            return None

    def extract_full(self, pdf_path: Path | str) -> dict | None:
        """
        Extrait le document complet (métadonnées + texte structuré).

        Args:
            pdf_path: Chemin vers le fichier PDF.

        Returns:
            Dict avec métadonnées et sections ou None.
        """
        if not self.available:
            return None

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return None

        try:
            with open(pdf_path, "rb") as f:
                response = requests.post(
                    f"{self.grobid_url}/api/processFulltextDocument",
                    files={"input": (pdf_path.name, f, "application/pdf")},
                    data={
                        "consolidateHeader": "1",
                        "consolidateCitations": "0",
                        "includeRawAffiliations": "1",
                    },
                    timeout=120,
                )

            if response.status_code != 200:
                logger.warning(f"GROBID fulltext erreur {response.status_code}")
                return None

            return self._parse_tei_full(response.text)

        except requests.RequestException as e:
            logger.error(f"Erreur GROBID fulltext: {e}")
            return None

    def _parse_tei_header(self, tei_xml: str) -> GrobidMetadata:
        """Parse le XML TEI pour extraire les métadonnées."""
        metadata = GrobidMetadata()

        try:
            root = ET.fromstring(tei_xml)
        except ET.ParseError as e:
            logger.error(f"Erreur parsing XML TEI: {e}")
            return metadata

        # Titre
        title_elem = root.find(".//tei:titleStmt/tei:title", self.TEI_NS)
        if title_elem is not None and title_elem.text:
            metadata.title = self._clean_text(title_elem.text)

        # Auteurs
        for author in root.findall(".//tei:sourceDesc//tei:author", self.TEI_NS):
            author_info = self._parse_author(author)
            if author_info:
                metadata.authors.append(author_info)

        # Abstract
        abstract_elem = root.find(".//tei:profileDesc/tei:abstract", self.TEI_NS)
        if abstract_elem is not None:
            abstract_text = "".join(abstract_elem.itertext())
            metadata.abstract = self._clean_text(abstract_text)

        # Mots-clés
        for keyword in root.findall(".//tei:profileDesc/tei:textClass/tei:keywords//tei:term", self.TEI_NS):
            if keyword.text:
                metadata.keywords.append(keyword.text.strip())

        # DOI
        doi_elem = root.find(".//tei:idno[@type='DOI']", self.TEI_NS)
        if doi_elem is not None and doi_elem.text:
            metadata.doi = doi_elem.text.strip()

        # Date/Année
        date_elem = root.find(".//tei:publicationStmt/tei:date", self.TEI_NS)
        if date_elem is not None:
            when = date_elem.get("when", "")
            year_match = re.search(r"(\d{4})", when or date_elem.text or "")
            if year_match:
                metadata.year = int(year_match.group(1))

        # Journal
        journal_elem = root.find(".//tei:monogr/tei:title", self.TEI_NS)
        if journal_elem is not None and journal_elem.text:
            metadata.journal = journal_elem.text.strip()

        # Volume, pages
        volume_elem = root.find(".//tei:biblScope[@unit='volume']", self.TEI_NS)
        if volume_elem is not None and volume_elem.text:
            metadata.volume = volume_elem.text.strip()

        page_elem = root.find(".//tei:biblScope[@unit='page']", self.TEI_NS)
        if page_elem is not None:
            from_page = page_elem.get("from", "")
            to_page = page_elem.get("to", "")
            if from_page and to_page:
                metadata.pages = f"{from_page}-{to_page}"
            elif page_elem.text:
                metadata.pages = page_elem.text.strip()

        # Publisher
        publisher_elem = root.find(".//tei:publicationStmt/tei:publisher", self.TEI_NS)
        if publisher_elem is not None and publisher_elem.text:
            metadata.publisher = publisher_elem.text.strip()

        return metadata

    def _parse_author(self, author_elem) -> dict | None:
        """Parse un élément auteur TEI."""
        persname = author_elem.find("tei:persName", self.TEI_NS)
        if persname is None:
            return None

        # Nom complet
        forename = persname.find("tei:forename", self.TEI_NS)
        surname = persname.find("tei:surname", self.TEI_NS)

        name_parts = []
        if forename is not None and forename.text:
            name_parts.append(forename.text.strip())
        if surname is not None and surname.text:
            name_parts.append(surname.text.strip())

        if not name_parts:
            return None

        name = " ".join(name_parts)

        # Email
        email = None
        email_elem = author_elem.find("tei:email", self.TEI_NS)
        if email_elem is not None and email_elem.text:
            email = email_elem.text.strip()

        # Affiliation
        affiliation = None
        aff_elem = author_elem.find("tei:affiliation", self.TEI_NS)
        if aff_elem is not None:
            org_name = aff_elem.find("tei:orgName", self.TEI_NS)
            if org_name is not None and org_name.text:
                affiliation = org_name.text.strip()

        return {
            "name": name,
            "email": email,
            "affiliation": affiliation,
        }

    def extract_references(self, pdf_path: Path | str) -> list[GrobidReference]:
        """
        Extrait les références bibliographiques d'un PDF.

        Args:
            pdf_path: Chemin vers le fichier PDF.

        Returns:
            Liste de GrobidReference.
        """
        if not self.available:
            return []

        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            return []

        try:
            with open(pdf_path, "rb") as f:
                response = requests.post(
                    f"{self.grobid_url}/api/processReferences",
                    files={"input": (pdf_path.name, f, "application/pdf")},
                    data={"consolidateCitations": "1"},  # Enrichir via CrossRef
                    headers={"Accept": "application/xml"},
                    timeout=120,
                )

            if response.status_code != 200:
                logger.warning(f"GROBID references erreur {response.status_code}")
                return []

            return self._parse_references(response.text)

        except requests.RequestException as e:
            logger.error(f"Erreur GROBID references: {e}")
            return []

    def _parse_references(self, tei_xml: str) -> list[GrobidReference]:
        """Parse les références depuis le XML TEI."""
        references = []

        try:
            root = ET.fromstring(tei_xml)
        except ET.ParseError as e:
            logger.error(f"Erreur parsing XML références: {e}")
            return references

        # Trouver toutes les références bibliographiques
        for idx, bibl in enumerate(root.findall(".//tei:biblStruct", self.TEI_NS)):
            ref = GrobidReference(index=idx)

            # Titre de l'article
            title_elem = bibl.find(".//tei:analytic/tei:title", self.TEI_NS)
            if title_elem is not None:
                ref.title = self._clean_text("".join(title_elem.itertext()))

            # Si pas de titre dans analytic, chercher dans monogr (pour les livres)
            if not ref.title:
                title_elem = bibl.find(".//tei:monogr/tei:title", self.TEI_NS)
                if title_elem is not None:
                    ref.title = self._clean_text("".join(title_elem.itertext()))

            # Auteurs
            for author in bibl.findall(".//tei:analytic/tei:author", self.TEI_NS):
                author_name = self._parse_author_name(author)
                if author_name:
                    ref.authors.append(author_name)

            # Si pas d'auteurs dans analytic, chercher dans monogr
            if not ref.authors:
                for author in bibl.findall(".//tei:monogr/tei:author", self.TEI_NS):
                    author_name = self._parse_author_name(author)
                    if author_name:
                        ref.authors.append(author_name)

            # Année
            date_elem = bibl.find(".//tei:monogr/tei:imprint/tei:date", self.TEI_NS)
            if date_elem is not None:
                when = date_elem.get("when", "")
                year_match = re.search(r"(\d{4})", when or date_elem.text or "")
                if year_match:
                    ref.year = int(year_match.group(1))

            # Journal
            journal_elem = bibl.find(".//tei:monogr/tei:title[@level='j']", self.TEI_NS)
            if journal_elem is not None:
                ref.journal = self._clean_text("".join(journal_elem.itertext()))

            # Volume
            volume_elem = bibl.find(".//tei:biblScope[@unit='volume']", self.TEI_NS)
            if volume_elem is not None and volume_elem.text:
                ref.volume = volume_elem.text.strip()

            # Pages
            page_elem = bibl.find(".//tei:biblScope[@unit='page']", self.TEI_NS)
            if page_elem is not None:
                from_page = page_elem.get("from", "")
                to_page = page_elem.get("to", "")
                if from_page and to_page:
                    ref.pages = f"{from_page}-{to_page}"
                elif page_elem.text:
                    ref.pages = page_elem.text.strip()

            # DOI
            doi_elem = bibl.find(".//tei:idno[@type='DOI']", self.TEI_NS)
            if doi_elem is not None and doi_elem.text:
                ref.doi = doi_elem.text.strip()

            # URL
            ptr_elem = bibl.find(".//tei:ptr[@type='url']", self.TEI_NS)
            if ptr_elem is not None:
                ref.url = ptr_elem.get("target", "")

            # Publisher
            publisher_elem = bibl.find(".//tei:monogr/tei:imprint/tei:publisher", self.TEI_NS)
            if publisher_elem is not None and publisher_elem.text:
                ref.publisher = publisher_elem.text.strip()

            # Ajouter seulement si on a au moins un titre ou des auteurs
            if ref.title or ref.authors:
                references.append(ref)

        logger.info(f"Extrait {len(references)} références bibliographiques")
        return references

    def _parse_author_name(self, author_elem) -> str | None:
        """Parse le nom d'un auteur depuis un élément TEI."""
        persname = author_elem.find("tei:persName", self.TEI_NS)
        if persname is None:
            return None

        forename = persname.find("tei:forename", self.TEI_NS)
        surname = persname.find("tei:surname", self.TEI_NS)

        name_parts = []
        if forename is not None and forename.text:
            name_parts.append(forename.text.strip())
        if surname is not None and surname.text:
            name_parts.append(surname.text.strip())

        return " ".join(name_parts) if name_parts else None

    def _parse_tei_full(self, tei_xml: str) -> dict:
        """Parse le document TEI complet."""
        result = {
            "metadata": self._parse_tei_header(tei_xml),
            "sections": [],
            "references": [],
        }

        try:
            root = ET.fromstring(tei_xml)
        except ET.ParseError:
            return result

        # Extraire les sections
        body = root.find(".//tei:body", self.TEI_NS)
        if body is not None:
            for div in body.findall("tei:div", self.TEI_NS):
                head = div.find("tei:head", self.TEI_NS)
                section_title = head.text if head is not None and head.text else "Untitled"

                paragraphs = []
                for p in div.findall("tei:p", self.TEI_NS):
                    text = "".join(p.itertext())
                    if text.strip():
                        paragraphs.append(self._clean_text(text))

                if paragraphs:
                    result["sections"].append({
                        "title": section_title,
                        "text": "\n\n".join(paragraphs),
                    })

        # Extraire les références depuis le back matter
        back = root.find(".//tei:back", self.TEI_NS)
        if back is not None:
            for idx, bibl in enumerate(back.findall(".//tei:biblStruct", self.TEI_NS)):
                ref = self._parse_single_reference(bibl, idx)
                if ref:
                    result["references"].append(ref)

        return result

    def _parse_single_reference(self, bibl, idx: int) -> GrobidReference | None:
        """Parse une seule référence bibliographique."""
        ref = GrobidReference(index=idx)

        # Titre
        title_elem = bibl.find(".//tei:analytic/tei:title", self.TEI_NS)
        if title_elem is not None:
            ref.title = self._clean_text("".join(title_elem.itertext()))
        if not ref.title:
            title_elem = bibl.find(".//tei:monogr/tei:title", self.TEI_NS)
            if title_elem is not None:
                ref.title = self._clean_text("".join(title_elem.itertext()))

        # Auteurs
        for author in bibl.findall(".//tei:analytic/tei:author", self.TEI_NS):
            author_name = self._parse_author_name(author)
            if author_name:
                ref.authors.append(author_name)
        if not ref.authors:
            for author in bibl.findall(".//tei:monogr/tei:author", self.TEI_NS):
                author_name = self._parse_author_name(author)
                if author_name:
                    ref.authors.append(author_name)

        # Année
        date_elem = bibl.find(".//tei:monogr/tei:imprint/tei:date", self.TEI_NS)
        if date_elem is not None:
            when = date_elem.get("when", "")
            year_match = re.search(r"(\d{4})", when or date_elem.text or "")
            if year_match:
                ref.year = int(year_match.group(1))

        # Journal
        journal_elem = bibl.find(".//tei:monogr/tei:title[@level='j']", self.TEI_NS)
        if journal_elem is not None:
            ref.journal = self._clean_text("".join(journal_elem.itertext()))

        # Volume
        volume_elem = bibl.find(".//tei:biblScope[@unit='volume']", self.TEI_NS)
        if volume_elem is not None and volume_elem.text:
            ref.volume = volume_elem.text.strip()

        # Pages
        page_elem = bibl.find(".//tei:biblScope[@unit='page']", self.TEI_NS)
        if page_elem is not None:
            from_page = page_elem.get("from", "")
            to_page = page_elem.get("to", "")
            if from_page and to_page:
                ref.pages = f"{from_page}-{to_page}"
            elif page_elem.text:
                ref.pages = page_elem.text.strip()

        # DOI
        doi_elem = bibl.find(".//tei:idno[@type='DOI']", self.TEI_NS)
        if doi_elem is not None and doi_elem.text:
            ref.doi = doi_elem.text.strip()

        if ref.title or ref.authors:
            return ref
        return None

    def _clean_text(self, text: str) -> str:
        """Nettoie le texte extrait."""
        if not text:
            return ""
        # Supprimer les espaces multiples et les retours à la ligne excessifs
        text = re.sub(r"\s+", " ", text)
        return text.strip()


# Instance globale avec configuration depuis settings
_grobid_client: GrobidClient | None = None


def get_grobid_client(grobid_url: str | None = None) -> GrobidClient:
    """Retourne l'instance du client GROBID."""
    global _grobid_client
    if _grobid_client is None:
        url = grobid_url or "http://localhost:8070"
        _grobid_client = GrobidClient(grobid_url=url)
    return _grobid_client

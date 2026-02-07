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

    def _parse_tei_full(self, tei_xml: str) -> dict:
        """Parse le document TEI complet."""
        result = {
            "metadata": self._parse_tei_header(tei_xml),
            "sections": [],
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

        return result

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

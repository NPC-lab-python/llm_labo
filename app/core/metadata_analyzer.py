"""Analyse et quantification de la qualité des métadonnées."""

import re
from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class MetadataQualityReport:
    """Rapport de qualité des métadonnées d'un document."""

    score: float  # Score global de 0 à 1
    details: dict[str, Any]  # Détails par champ
    suggestions: list[str]  # Suggestions d'amélioration


class MetadataAnalyzer:
    """Analyseur de qualité des métadonnées."""

    # Poids de chaque champ dans le score global
    FIELD_WEIGHTS = {
        "title": 0.30,       # Très important
        "authors": 0.25,     # Important
        "year": 0.20,        # Important
        "abstract": 0.15,    # Utile
        "keywords": 0.10,    # Bonus
    }

    def analyze(
        self,
        title: str | None,
        authors: str | None,
        year: int | None,
        abstract: str | None = None,
        keywords: str | None = None,
    ) -> MetadataQualityReport:
        """
        Analyse la qualité des métadonnées d'un document.

        Args:
            title: Titre du document.
            authors: Auteurs (string ou JSON).
            year: Année de publication.
            abstract: Résumé du document.
            keywords: Mots-clés.

        Returns:
            MetadataQualityReport avec score et détails.
        """
        details = {}
        suggestions = []

        # Analyse du titre
        title_score, title_details = self._analyze_title(title)
        details["title"] = title_details
        if title_score < 1.0:
            suggestions.extend(title_details.get("suggestions", []))

        # Analyse des auteurs
        authors_score, authors_details = self._analyze_authors(authors)
        details["authors"] = authors_details
        if authors_score < 1.0:
            suggestions.extend(authors_details.get("suggestions", []))

        # Analyse de l'année
        year_score, year_details = self._analyze_year(year)
        details["year"] = year_details
        if year_score < 1.0:
            suggestions.extend(year_details.get("suggestions", []))

        # Analyse du résumé
        abstract_score, abstract_details = self._analyze_abstract(abstract)
        details["abstract"] = abstract_details

        # Analyse des mots-clés
        keywords_score, keywords_details = self._analyze_keywords(keywords)
        details["keywords"] = keywords_details

        # Calcul du score global pondéré
        score = (
            title_score * self.FIELD_WEIGHTS["title"]
            + authors_score * self.FIELD_WEIGHTS["authors"]
            + year_score * self.FIELD_WEIGHTS["year"]
            + abstract_score * self.FIELD_WEIGHTS["abstract"]
            + keywords_score * self.FIELD_WEIGHTS["keywords"]
        )

        return MetadataQualityReport(
            score=round(score, 3),
            details=details,
            suggestions=suggestions,
        )

    def _analyze_title(self, title: str | None) -> tuple[float, dict]:
        """Analyse la qualité du titre."""
        if not title or not title.strip():
            return 0.0, {
                "present": False,
                "score": 0.0,
                "suggestions": ["Titre manquant - extraction manuelle recommandée"],
            }

        title = title.strip()
        issues = []
        score = 1.0

        # Vérifier si c'est juste un nom de fichier
        if title.endswith(".pdf") or "/" in title or "\\" in title:
            score = 0.2
            issues.append("Le titre semble être un nom de fichier")

        # Vérifier la longueur
        if len(title) < 10:
            score = min(score, 0.3)
            issues.append("Titre trop court")
        elif len(title) > 300:
            score = min(score, 0.7)
            issues.append("Titre anormalement long")

        # Vérifier si c'est tout en majuscules
        if title.isupper() and len(title) > 20:
            score = min(score, 0.8)
            issues.append("Titre entièrement en majuscules")

        # Vérifier les caractères suspects
        if re.search(r"[\x00-\x1f]", title):
            score = min(score, 0.5)
            issues.append("Caractères de contrôle dans le titre")

        return score, {
            "present": True,
            "value": title[:100] + "..." if len(title) > 100 else title,
            "length": len(title),
            "score": score,
            "issues": issues,
            "suggestions": [f"Titre: {issue}" for issue in issues] if issues else [],
        }

    def _analyze_authors(self, authors: str | None) -> tuple[float, dict]:
        """Analyse la qualité des auteurs."""
        if not authors or not authors.strip():
            return 0.0, {
                "present": False,
                "score": 0.0,
                "suggestions": ["Auteurs manquants"],
            }

        authors = authors.strip()
        issues = []
        score = 1.0

        # Vérifier si c'est un format JSON ou liste
        author_list = []
        if authors.startswith("["):
            try:
                import json
                author_list = json.loads(authors)
            except json.JSONDecodeError:
                author_list = [authors]
        else:
            # Séparer par virgule ou "and"
            author_list = re.split(r",|;| and | et ", authors)

        author_count = len([a for a in author_list if a.strip()])

        # Vérifier le format des noms
        valid_names = 0
        for author in author_list:
            author = author.strip()
            if author:
                # Un nom valide contient au moins 2 parties (prénom, nom)
                # ou est une initiale suivie d'un nom
                if re.match(r"^[A-Z][a-zéèêëàâäùûüîïôö\-\']+(\s+[A-Z][a-zéèêëàâäùûüîïôö\-\']*)+$", author):
                    valid_names += 1
                elif re.match(r"^[A-Z]\.\s*[A-Z][a-zéèêëàâäùûüîïôö\-\']+", author):
                    valid_names += 1

        if author_count > 0:
            name_quality = valid_names / author_count
            if name_quality < 0.5:
                score = 0.6
                issues.append("Format des noms d'auteurs non standard")
        else:
            score = 0.3
            issues.append("Aucun auteur identifiable")

        return score, {
            "present": True,
            "value": authors[:100] + "..." if len(authors) > 100 else authors,
            "count": author_count,
            "score": score,
            "issues": issues,
            "suggestions": [f"Auteurs: {issue}" for issue in issues] if issues else [],
        }

    def _analyze_year(self, year: int | None) -> tuple[float, dict]:
        """Analyse la qualité de l'année."""
        if year is None:
            return 0.0, {
                "present": False,
                "score": 0.0,
                "suggestions": ["Année de publication manquante"],
            }

        issues = []
        score = 1.0

        # Vérifier la plausibilité
        from datetime import datetime
        current_year = datetime.now().year

        if year < 1900:
            score = 0.3
            issues.append(f"Année suspecte ({year}) - trop ancienne")
        elif year > current_year + 1:
            score = 0.2
            issues.append(f"Année impossible ({year}) - dans le futur")
        elif year < 1950:
            score = 0.8
            issues.append(f"Année ancienne ({year}) - vérifier si correcte")

        return score, {
            "present": True,
            "value": year,
            "score": score,
            "issues": issues,
            "suggestions": [f"Année: {issue}" for issue in issues] if issues else [],
        }

    def _analyze_abstract(self, abstract: str | None) -> tuple[float, dict]:
        """Analyse la qualité du résumé."""
        if not abstract or not abstract.strip():
            return 0.0, {
                "present": False,
                "score": 0.0,
            }

        abstract = abstract.strip()
        score = 1.0

        # Un bon résumé fait entre 100 et 500 mots
        word_count = len(abstract.split())
        if word_count < 50:
            score = 0.5
        elif word_count < 100:
            score = 0.8

        return score, {
            "present": True,
            "word_count": word_count,
            "score": score,
        }

    def _analyze_keywords(self, keywords: str | None) -> tuple[float, dict]:
        """Analyse la qualité des mots-clés."""
        if not keywords or not keywords.strip():
            return 0.0, {
                "present": False,
                "score": 0.0,
            }

        # Compter les mots-clés
        if keywords.startswith("["):
            try:
                import json
                kw_list = json.loads(keywords)
                count = len(kw_list)
            except json.JSONDecodeError:
                count = 1
        else:
            count = len(keywords.split(","))

        score = min(1.0, count / 3)  # Score max avec 3+ mots-clés

        return score, {
            "present": True,
            "count": count,
            "score": score,
        }


# Instance globale
metadata_analyzer = MetadataAnalyzer()

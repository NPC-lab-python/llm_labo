#!/usr/bin/env python
"""Met à jour les métadonnées des documents existants avec l'extracteur amélioré."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from tqdm import tqdm

from app.core.pdf_extractor import pdf_extractor
from app.core.metadata_analyzer import metadata_analyzer
from app.models.database import Document, SessionLocal, init_db
from config import settings


def update_metadata(limit: int | None = None, dry_run: bool = False):
    """
    Met à jour les métadonnées des documents existants.

    Args:
        limit: Nombre max de documents à traiter (None = tous)
        dry_run: Si True, n'enregistre pas les modifications
    """
    init_db()
    db = SessionLocal()

    try:
        # Récupérer les documents indexés
        query = db.query(Document).filter(Document.status == "indexed")
        if limit:
            query = query.limit(limit)

        documents = query.all()
        print(f"Documents à traiter: {len(documents)}")

        if not documents:
            print("Aucun document à traiter.")
            return

        # Statistiques
        stats = {
            "processed": 0,
            "updated": 0,
            "errors": 0,
            "title_improved": 0,
            "authors_added": 0,
            "year_added": 0,
            "score_improved": 0,
        }

        for doc in tqdm(documents, desc="Mise à jour des métadonnées"):
            try:
                file_path = Path(doc.file_path)

                if not file_path.exists():
                    tqdm.write(f"  Fichier non trouvé: {file_path.name}")
                    stats["errors"] += 1
                    continue

                # Extraire les nouvelles métadonnées
                content = pdf_extractor.extract(file_path)
                new_meta = content.metadata

                # Comparer avec les anciennes
                changes = []

                # Titre
                old_title = doc.title or ""
                new_title = new_meta.title or ""
                if new_title and new_title != old_title:
                    # Vérifier si le nouveau titre est meilleur
                    old_valid = metadata_analyzer._analyze_title(old_title)[0]
                    new_valid = metadata_analyzer._analyze_title(new_title)[0]
                    if new_valid > old_valid:
                        changes.append(f"titre: '{old_title[:30]}...' -> '{new_title[:30]}...'")
                        if not dry_run:
                            doc.title = new_title
                        stats["title_improved"] += 1

                # Auteurs
                old_authors = doc.authors or ""
                new_authors = new_meta.authors or ""
                if new_authors and not old_authors:
                    changes.append(f"auteurs: ajouté '{new_authors[:40]}...'")
                    if not dry_run:
                        doc.authors = new_authors
                    stats["authors_added"] += 1
                elif new_authors and new_authors != old_authors:
                    # Vérifier si les nouveaux auteurs sont meilleurs
                    old_valid = metadata_analyzer._analyze_authors(old_authors)[0]
                    new_valid = metadata_analyzer._analyze_authors(new_authors)[0]
                    if new_valid > old_valid:
                        changes.append(f"auteurs: '{old_authors[:30]}...' -> '{new_authors[:30]}...'")
                        if not dry_run:
                            doc.authors = new_authors
                        stats["authors_added"] += 1

                # Année
                old_year = doc.publication_year
                new_year = new_meta.year
                if new_year and not old_year:
                    changes.append(f"année: ajouté {new_year}")
                    if not dry_run:
                        doc.publication_year = new_year
                    stats["year_added"] += 1
                elif new_year and old_year and new_year != old_year:
                    # Préférer l'année la plus récente si plausible
                    if 1950 <= new_year <= 2026:
                        changes.append(f"année: {old_year} -> {new_year}")
                        if not dry_run:
                            doc.publication_year = new_year
                        stats["year_added"] += 1

                # Recalculer le score de qualité
                old_score = doc.metadata_quality_score or 0.0
                quality_report = metadata_analyzer.analyze(
                    title=doc.title if dry_run else (new_meta.title or doc.title),
                    authors=doc.authors if dry_run else (new_meta.authors or doc.authors),
                    year=doc.publication_year if dry_run else (new_meta.year or doc.publication_year),
                )
                new_score = quality_report.score

                if new_score > old_score:
                    stats["score_improved"] += 1
                    if not dry_run:
                        doc.metadata_quality_score = new_score

                if changes:
                    stats["updated"] += 1
                    if limit and limit <= 20:  # Afficher les détails si peu de docs
                        tqdm.write(f"\n  {doc.title[:50]}...")
                        for change in changes:
                            tqdm.write(f"    - {change}")
                        tqdm.write(f"    Score: {old_score:.2f} -> {new_score:.2f}")

                stats["processed"] += 1

            except Exception as e:
                tqdm.write(f"  Erreur sur {doc.id}: {e}")
                stats["errors"] += 1

        # Sauvegarder les modifications
        if not dry_run:
            db.commit()
            print("\nModifications enregistrées.")
        else:
            print("\n[DRY RUN] Aucune modification enregistrée.")

        # Afficher les statistiques
        print("\n" + "=" * 60)
        print("STATISTIQUES")
        print("=" * 60)
        print(f"  Documents traités: {stats['processed']}")
        print(f"  Documents mis à jour: {stats['updated']}")
        print(f"  Erreurs: {stats['errors']}")
        print()
        print(f"  Titres améliorés: {stats['title_improved']}")
        print(f"  Auteurs ajoutés/améliorés: {stats['authors_added']}")
        print(f"  Années ajoutées/corrigées: {stats['year_added']}")
        print(f"  Scores améliorés: {stats['score_improved']}")

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Met à jour les métadonnées des documents existants."
    )
    parser.add_argument(
        "-n", "--limit",
        type=int,
        default=None,
        help="Nombre max de documents à traiter"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simuler sans enregistrer les modifications"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Traiter tous les documents (ignore --limit)"
    )

    args = parser.parse_args()

    limit = None if args.all else args.limit

    print("=" * 60)
    print("MISE À JOUR DES MÉTADONNÉES")
    print("=" * 60)
    print(f"  Limite: {limit if limit else 'tous les documents'}")
    print(f"  Mode: {'simulation (dry-run)' if args.dry_run else 'réel'}")
    print()

    update_metadata(limit=limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

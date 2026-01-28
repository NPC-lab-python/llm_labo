#!/usr/bin/env python
"""Script d'indexation batch des documents PDF."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from config import settings
from app.models.database import init_db, SessionLocal
from app.services.indexing_service import indexing_service


def main():
    """Point d'entrée principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Indexe les fichiers PDF pour la recherche RAG"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=str(settings.pdf_dir),
        help=f"Dossier contenant les PDFs (défaut: {settings.pdf_dir})",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Afficher plus de détails",
    )

    args = parser.parse_args()

    # Configuration du logging
    if args.verbose:
        logger.level("DEBUG")
    else:
        logger.level("INFO")

    folder = Path(args.folder)

    if not folder.exists():
        logger.error(f"Dossier non trouvé: {folder}")
        sys.exit(1)

    pdf_count = len(list(folder.glob("*.pdf")))
    if pdf_count == 0:
        logger.warning(f"Aucun fichier PDF trouvé dans {folder}")
        sys.exit(0)

    logger.info(f"Indexation de {pdf_count} fichiers PDF depuis {folder}")

    # Initialisation
    settings.ensure_directories()
    init_db()

    # Indexation
    db = SessionLocal()
    try:
        result = indexing_service.index_folder(db, folder)

        logger.info("=" * 50)
        logger.info("RÉSUMÉ DE L'INDEXATION")
        logger.info("=" * 50)
        logger.info(f"Documents traités: {result.processed}")
        logger.info(f"Erreurs: {len(result.errors)}")

        if result.errors:
            logger.warning("Erreurs rencontrées:")
            for error in result.errors:
                logger.warning(f"  - {error}")

        logger.info("=" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    main()

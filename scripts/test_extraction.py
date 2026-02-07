#!/usr/bin/env python
"""Test de l'extraction de métadonnées sur un échantillon de PDFs."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import random
from app.core.pdf_extractor import pdf_extractor
from config import settings


def test_extraction(num_samples: int = 10):
    """Teste l'extraction sur un échantillon de PDFs."""
    pdf_dir = Path(settings.pdf_dir)

    if not pdf_dir.exists():
        print(f"Répertoire non trouvé: {pdf_dir}")
        return

    # Lister tous les PDFs
    all_pdfs = list(pdf_dir.glob("**/*.pdf"))
    print(f"Trouvé {len(all_pdfs)} PDFs")

    if not all_pdfs:
        return

    # Sélectionner un échantillon aléatoire
    sample_size = min(num_samples, len(all_pdfs))
    sample = random.sample(all_pdfs, sample_size)

    print(f"\nTest sur {sample_size} PDFs:\n")
    print("=" * 80)

    results = {
        "title_extracted": 0,
        "authors_extracted": 0,
        "year_extracted": 0,
        "all_extracted": 0,
    }

    for pdf_path in sample:
        try:
            content = pdf_extractor.extract(pdf_path)
            meta = content.metadata

            print(f"\nFichier: {pdf_path.name[:50]}...")
            print(f"  Titre: {meta.title[:70] if meta.title else 'N/A'}...")
            print(f"  Auteurs: {meta.authors[:70] if meta.authors else 'N/A'}")
            print(f"  Année: {meta.year if meta.year else 'N/A'}")

            # Comptage
            if meta.title and len(meta.title) > 5:
                results["title_extracted"] += 1
            if meta.authors and len(meta.authors) > 2:
                results["authors_extracted"] += 1
            if meta.year:
                results["year_extracted"] += 1
            if meta.title and meta.authors and meta.year:
                results["all_extracted"] += 1

        except Exception as e:
            print(f"\nErreur sur {pdf_path.name}: {e}")

    print("\n" + "=" * 80)
    print(f"\nRésultats ({sample_size} PDFs):")
    print(f"  - Titre extrait: {results['title_extracted']} ({100*results['title_extracted']/sample_size:.0f}%)")
    print(f"  - Auteurs extraits: {results['authors_extracted']} ({100*results['authors_extracted']/sample_size:.0f}%)")
    print(f"  - Année extraite: {results['year_extracted']} ({100*results['year_extracted']/sample_size:.0f}%)")
    print(f"  - Tout extrait: {results['all_extracted']} ({100*results['all_extracted']/sample_size:.0f}%)")


if __name__ == "__main__":
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    test_extraction(num)

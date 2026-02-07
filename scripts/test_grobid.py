#!/usr/bin/env python
"""Test de l'intégration GROBID."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.grobid_client import get_grobid_client
from app.core.pdf_extractor import PDFExtractor
from config import settings


def test_grobid_availability():
    """Teste si GROBID est disponible."""
    print("=" * 60)
    print("Test de disponibilité GROBID")
    print("=" * 60)

    client = get_grobid_client(settings.grobid_url)
    print(f"URL GROBID: {settings.grobid_url}")
    print(f"GROBID disponible: {client.available}")

    return client.available


def test_extraction_comparison():
    """Compare l'extraction PyMuPDF vs GROBID."""
    print("\n" + "=" * 60)
    print("Comparaison extraction PyMuPDF vs GROBID")
    print("=" * 60)

    # Trouver quelques PDFs de test
    pdf_files = list(settings.pdf_dir.glob("*.pdf"))[:3]

    if not pdf_files:
        print("Aucun PDF trouvé dans", settings.pdf_dir)
        return

    # Extracteur sans GROBID
    extractor_pymupdf = PDFExtractor(use_grobid=False)

    # Extracteur avec GROBID
    extractor_grobid = PDFExtractor(use_grobid=True)
    grobid_available = extractor_grobid._grobid_client and extractor_grobid._grobid_client.available

    for pdf_path in pdf_files:
        print(f"\n--- {pdf_path.name} ---")

        # Extraction PyMuPDF
        result_pymupdf = extractor_pymupdf.extract(pdf_path)
        meta_pymupdf = result_pymupdf.metadata

        print(f"\nPyMuPDF:")
        print(f"  Titre: {meta_pymupdf.title[:60] if meta_pymupdf.title else 'N/A'}...")
        print(f"  Auteurs: {meta_pymupdf.authors[:60] if meta_pymupdf.authors else 'N/A'}...")
        print(f"  Année: {meta_pymupdf.year}")
        print(f"  Méthode: {meta_pymupdf.extraction_method}")

        if grobid_available:
            # Extraction GROBID
            result_grobid = extractor_grobid.extract(pdf_path)
            meta_grobid = result_grobid.metadata

            print(f"\nGROBID:")
            print(f"  Titre: {meta_grobid.title[:60] if meta_grobid.title else 'N/A'}...")
            print(f"  Auteurs: {meta_grobid.authors[:60] if meta_grobid.authors else 'N/A'}...")
            print(f"  Année: {meta_grobid.year}")
            print(f"  Abstract: {meta_grobid.abstract[:80] if meta_grobid.abstract else 'N/A'}...")
            print(f"  DOI: {meta_grobid.doi or 'N/A'}")
            print(f"  Journal: {meta_grobid.journal or 'N/A'}")
            print(f"  Keywords: {meta_grobid.keywords[:3] if meta_grobid.keywords else 'N/A'}")
            print(f"  Méthode: {meta_grobid.extraction_method}")
        else:
            print("\nGROBID non disponible - extraction ignorée")


def main():
    """Point d'entrée principal."""
    grobid_ok = test_grobid_availability()

    if not grobid_ok:
        print("\n" + "=" * 60)
        print("GROBID n'est pas disponible.")
        print("Pour l'installer, suivez ces instructions:")
        print("  1. Docker: docker run -p 8070:8070 lfoppiano/grobid:0.8.0")
        print("  2. Ou téléchargez: https://github.com/kermitt2/grobid")
        print("=" * 60)

    test_extraction_comparison()


if __name__ == "__main__":
    main()

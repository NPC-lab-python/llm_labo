#!/usr/bin/env python
"""Migration: Ajoute la colonne metadata_quality_score à la table documents."""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3

from config import settings


def migrate():
    """Ajoute la colonne metadata_quality_score si elle n'existe pas."""
    db_path = settings.sqlite_path

    if not db_path.exists():
        print(f"Base de données non trouvée: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Vérifier si la colonne existe déjà
    cursor.execute("PRAGMA table_info(documents)")
    columns = [row[1] for row in cursor.fetchall()]

    if "metadata_quality_score" in columns:
        print("La colonne metadata_quality_score existe déjà.")
    else:
        print("Ajout de la colonne metadata_quality_score...")
        cursor.execute("""
            ALTER TABLE documents
            ADD COLUMN metadata_quality_score REAL DEFAULT 0.0
        """)
        conn.commit()
        print("Migration terminée avec succès.")

    conn.close()


if __name__ == "__main__":
    migrate()

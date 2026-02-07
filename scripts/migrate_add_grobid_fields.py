#!/usr/bin/env python
"""Migration pour ajouter les champs GROBID à la table documents."""

import sqlite3
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


def migrate():
    """Ajoute les colonnes doi, journal et extraction_method."""
    db_path = settings.sqlite_path

    if not db_path.exists():
        print(f"Base de données non trouvée: {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Vérifier les colonnes existantes
    cursor.execute("PRAGMA table_info(documents)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    migrations = [
        ("doi", "VARCHAR(100)"),
        ("journal", "TEXT"),
        ("extraction_method", "VARCHAR(20) DEFAULT 'pymupdf'"),
    ]

    added = []
    for col_name, col_type in migrations:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
                print(f"Colonne '{col_name}' ajoutée")
            except sqlite3.OperationalError as e:
                print(f"Erreur pour '{col_name}': {e}")
        else:
            print(f"Colonne '{col_name}' existe déjà")

    conn.commit()
    conn.close()

    if added:
        print(f"\nMigration terminée: {len(added)} colonne(s) ajoutée(s)")
    else:
        print("\nAucune migration nécessaire")

    return True


if __name__ == "__main__":
    migrate()

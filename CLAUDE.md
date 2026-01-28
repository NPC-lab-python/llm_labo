# LLM Labo - Système RAG pour Articles de Recherche

## Projet
Système RAG (Retrieval-Augmented Generation) pour rechercher et citer des articles et thèses de recherche. Utilise Claude (Anthropic) comme LLM, Voyage AI pour les embeddings et ChromaDB comme base vectorielle.

## Environnement
- **Langage** : Python 3.11
- **Environnement** : Conda (`rag_env`)
- **IDE** : PyCharm
- **OS** : Windows
- **LLM** : Claude API (Anthropic)
- **Embeddings** : Voyage AI

## Stack Technique
- **API** : FastAPI + Uvicorn
- **Base vectorielle** : ChromaDB
- **Métadonnées** : SQLite + SQLAlchemy
- **PDF** : PyMuPDF
- **LLM** : anthropic (claude-sonnet-4-20250514)
- **Embeddings** : voyageai (voyage-3)

## Conventions de Code
- Indentation : 4 espaces
- Langue des commentaires : Français
- Docstrings : Format Google
- Type hints obligatoires

## Commandes Utiles
```bash
# Créer l'environnement
conda env create -f environment.yml
conda activate rag_env

# Configurer les clés API
cp .env.example .env
# Éditer .env avec:
# - ANTHROPIC_API_KEY (pour Claude)
# - VOYAGE_API_KEY (pour les embeddings)

# Lancer l'API
python main.py
# ou
uvicorn app.api.main:app --reload

# Indexer les PDFs
python scripts/index_all.py ./data/pdfs

# Tests
pytest
```

## Structure du Projet
```
llm_labo/
├── main.py                 # Point d'entrée API
├── environment.yml         # Dépendances Conda
├── .env                    # Configuration (ANTHROPIC_API_KEY, VOYAGE_API_KEY)
├── config/
│   └── settings.py         # Configuration Pydantic
├── app/
│   ├── api/
│   │   ├── main.py         # Application FastAPI
│   │   └── routes/         # Endpoints API
│   ├── core/
│   │   ├── pdf_extractor.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── retriever.py
│   │   └── generator.py
│   ├── models/
│   │   ├── schemas.py      # Schemas Pydantic
│   │   └── database.py     # Modèles SQLAlchemy
│   └── services/
│       ├── indexing_service.py
│       └── query_service.py
├── data/
│   ├── pdfs/               # PDFs à indexer
│   ├── chroma_db/          # Base vectorielle
│   └── metadata.db         # SQLite
└── scripts/
    └── index_all.py        # Indexation batch
```

## Endpoints API
| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/query` | POST | Poser une question |
| `/api/v1/index` | POST | Indexer un PDF |
| `/api/v1/index/batch` | POST | Indexer un dossier |
| `/api/v1/documents` | GET | Lister les documents |
| `/api/v1/health` | GET | État du système |

## Notes Importantes
- Toujours répondre en français sauf si demandé autrement
- Les PDFs sont dans `data/pdfs/`
- La documentation API est sur http://localhost:8000/docs

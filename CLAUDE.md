# LLM Labo - Système RAG pour Articles de Recherche

## Projet
Système RAG (Retrieval-Augmented Generation) pour rechercher et citer des articles et thèses de recherche. Utilise Claude (Anthropic) comme LLM, Voyage AI pour les embeddings et ChromaDB comme base vectorielle.

## Environnement
- **Langage** : Python 3.11 + TypeScript
- **Environnement** : Conda (`rag_env`) + Node.js
- **IDE** : PyCharm
- **OS** : Windows
- **LLM** : Claude API (Anthropic)
- **Embeddings** : Voyage AI

## Stack Technique

### Backend
- **API** : FastAPI + Uvicorn
- **Base vectorielle** : ChromaDB
- **Métadonnées** : SQLite + SQLAlchemy
- **PDF** : PyMuPDF
- **LLM** : anthropic (claude-sonnet-4-20250514)
- **Embeddings** : voyageai (voyage-3)

### Frontend
- **Framework** : React 18 + TypeScript
- **Build** : Vite
- **Styling** : Tailwind CSS (dark mode inclus)
- **State** : Zustand + React Query
- **Graphiques** : Recharts
- **Icônes** : Lucide React

## Conventions de Code
- Indentation : 4 espaces (Python), 2 espaces (TypeScript)
- Langue des commentaires : Français
- Docstrings : Format Google
- Type hints obligatoires

## Commandes Utiles
```bash
# Créer l'environnement Python
conda env create -f environment.yml
conda activate rag_env

# Configurer les clés API
cp .env.example .env
# Éditer .env avec:
# - ANTHROPIC_API_KEY (pour Claude)
# - VOYAGE_API_KEY (pour les embeddings)

# Lancer l'API backend
python main.py
# ou
uvicorn app.api.main:app --reload

# Installer les dépendances frontend
cd frontend && npm install

# Lancer le frontend (dev)
cd frontend && npm run dev

# Builder le frontend (production)
cd frontend && npm run build

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
│   │   ├── main.py         # Application FastAPI + CORS
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
├── frontend/               # Interface React
│   ├── package.json
│   ├── vite.config.ts      # Proxy vers l'API
│   ├── tailwind.config.js
│   └── src/
│       ├── api/            # Client API + types
│       ├── hooks/          # React Query hooks
│       ├── stores/         # Zustand stores
│       ├── components/     # UI, layout, chat, documents, dashboard
│       └── pages/          # ChatPage, DocumentsPage, DashboardPage
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
| `/api/v1/index` | POST | Indexer un PDF (par chemin) |
| `/api/v1/index/batch` | POST | Indexer un dossier |
| `/api/v1/upload` | POST | Uploader et indexer un PDF |
| `/api/v1/index/reindex` | POST | Réindexer les embeddings |
| `/api/v1/documents` | GET | Lister les documents (paginé) |
| `/api/v1/documents/{id}` | GET | Détails d'un document |
| `/api/v1/documents/{id}` | DELETE | Supprimer un document |
| `/api/v1/stats` | GET | Statistiques de qualité |
| `/api/v1/health` | GET | État du système |

## Interface Web

L'interface est accessible sur :
- **Développement** : http://localhost:5173 (Vite dev server)
- **Production** : http://localhost:8000 (servie par FastAPI)

### Pages
- **Chat** : Page principale pour poser des questions avec filtres (année, auteurs)
- **Documents** : Table paginée avec upload drag & drop, recherche et suppression
- **Indexation** : Indexation par dossier et mise à jour des embeddings
- **Dashboard** : Statistiques, état des services, graphiques de qualité

## Notes Importantes
- Toujours répondre en français sauf si demandé autrement
- Les PDFs sont dans `data/pdfs/`
- La documentation API est sur http://localhost:8000/docs
- Le frontend en production est servi automatiquement depuis `frontend/dist/`

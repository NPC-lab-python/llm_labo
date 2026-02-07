"""Application FastAPI principale."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings
from app.models.database import init_db
from app.api.routes import query, index, documents, projects


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestion du cycle de vie de l'application."""
    # Startup
    logger.info("Démarrage de l'API RAG")
    settings.ensure_directories()
    init_db()
    logger.info("Base de données initialisée")

    yield

    # Shutdown
    logger.info("Arrêt de l'API RAG")


app = FastAPI(
    title="RAG API - Recherche Articles",
    description="API de recherche sémantique dans les articles et thèses de recherche",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS pour le développement
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(index.router, prefix="/api/v1", tags=["Index"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(projects.router, prefix="/api/v1", tags=["Projects"])


@app.get("/api/v1/health")
async def health_check():
    """Vérifie l'état de santé du système."""
    from app.core.retriever import get_retriever
    from app.models.database import SessionLocal

    # Vérification ChromaDB
    try:
        retriever = get_retriever()
        stats = retriever.get_stats()
        chroma_status = "ok"
        doc_count = stats["total_chunks"]
    except Exception as e:
        chroma_status = f"error: {e}"
        doc_count = 0

    # Vérification Claude (Anthropic)
    claude_status = "ok" if settings.anthropic_api_key else "not_configured"

    # Vérification Voyage AI
    voyage_status = "ok" if settings.voyage_api_key else "not_configured"

    return {
        "status": "ok",
        "chroma_status": chroma_status,
        "claude_status": claude_status,
        "voyage_status": voyage_status,
        "document_count": doc_count,
    }


# Servir les fichiers statiques du frontend en production
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )

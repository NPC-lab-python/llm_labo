"""Application FastAPI principale."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger

from config import settings
from app.models.database import init_db
from app.api.routes import query, index, documents


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

# Inclusion des routes
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(index.router, prefix="/api/v1", tags=["Index"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])


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

    # Vérification Mistral
    mistral_status = "configured" if settings.mistral_api_key else "not_configured"

    return {
        "status": "ok",
        "chroma_status": chroma_status,
        "mistral_status": mistral_status,
        "document_count": doc_count,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )

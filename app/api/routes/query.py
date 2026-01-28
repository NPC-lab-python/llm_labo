"""Routes pour les requêtes RAG."""

from fastapi import APIRouter

from app.models.schemas import QueryRequest, QueryResponse
from app.services.query_service import query_service

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    """
    Pose une question et obtient une réponse basée sur les documents indexés.

    - **question**: La question à poser
    - **top_k**: Nombre de sources à consulter (défaut: 5)
    - **year_min**: Filtrer par année minimum
    - **year_max**: Filtrer par année maximum
    - **authors**: Filtrer par auteurs

    Retourne une réponse avec les sources citées.
    """
    return query_service.query(request)

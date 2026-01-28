"""Routes pour l'indexation des documents."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.models.schemas import IndexRequest, IndexResponse, BatchIndexRequest, BatchIndexResponse
from app.services.indexing_service import indexing_service

router = APIRouter()


@router.post("/index", response_model=IndexResponse)
async def index_document(
    request: IndexRequest,
    db: Session = Depends(get_db),
) -> IndexResponse:
    """
    Indexe un fichier PDF.

    - **file_path**: Chemin vers le fichier PDF
    - **title**: Titre du document (optionnel)
    - **authors**: Liste des auteurs (optionnel)
    - **year**: Année de publication (optionnel)

    Les métadonnées sont extraites automatiquement du PDF si non fournies.
    """
    try:
        return indexing_service.index_document(
            db=db,
            file_path=request.file_path,
            title=request.title,
            authors=request.authors,
            year=request.year,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'indexation: {e}")


@router.post("/index/batch", response_model=BatchIndexResponse)
async def index_batch(
    request: BatchIndexRequest,
    db: Session = Depends(get_db),
) -> BatchIndexResponse:
    """
    Indexe tous les fichiers PDF d'un dossier.

    - **folder_path**: Chemin vers le dossier contenant les PDFs

    Retourne le nombre de documents traités et les erreurs éventuelles.
    """
    try:
        return indexing_service.index_folder(
            db=db,
            folder_path=request.folder_path,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'indexation batch: {e}")

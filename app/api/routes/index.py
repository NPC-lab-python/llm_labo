"""Routes pour l'indexation des documents."""

import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from config import settings
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


@router.post("/upload", response_model=IndexResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IndexResponse:
    """
    Upload et indexe un fichier PDF.

    - **file**: Fichier PDF à uploader

    Le fichier est sauvegardé dans le dossier data/pdfs/ puis indexé.
    """
    # Vérifier que c'est un PDF
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers PDF sont acceptés")

    # Créer un nom de fichier sécurisé
    safe_filename = Path(file.filename).name
    pdf_path = settings.pdf_directory / safe_filename

    # Éviter l'écrasement
    counter = 1
    while pdf_path.exists():
        stem = Path(safe_filename).stem
        pdf_path = settings.pdf_directory / f"{stem}_{counter}.pdf"
        counter += 1

    try:
        # Sauvegarder le fichier
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Indexer le document
        return indexing_service.index_document(
            db=db,
            file_path=str(pdf_path),
        )
    except Exception as e:
        # Supprimer le fichier en cas d'erreur
        if pdf_path.exists():
            pdf_path.unlink()
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'upload: {e}")


@router.post("/index/reindex")
async def reindex_embeddings(
    document_id: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Réindexe les embeddings d'un ou tous les documents.

    - **document_id**: ID du document (optionnel, tous si non fourni)

    Utile après un changement de modèle d'embedding ou pour mettre à jour
    les embeddings avec les métadonnées enrichies.
    """
    try:
        result = indexing_service.reindex_embeddings(
            db=db,
            document_id=document_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de réindexation: {e}")


@router.post("/index/reset")
async def reset_databases(
    db: Session = Depends(get_db),
):
    """
    Réinitialise complètement les bases de données.

    Supprime tous les documents et chunks de SQLite et ChromaDB.
    À utiliser avant une réindexation complète avec GROBID.
    """
    try:
        result = indexing_service.reset_all(db=db)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de réinitialisation: {e}")

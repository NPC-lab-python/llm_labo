"""Routes pour la gestion des documents."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.database import get_db, Document
from app.models.schemas import DocumentInfo, DocumentListResponse
from app.services.indexing_service import indexing_service

router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(default=1, ge=1, description="Numéro de page"),
    limit: int = Query(default=20, ge=1, le=100, description="Documents par page"),
    status: str | None = Query(default=None, description="Filtrer par statut"),
    search: str | None = Query(default=None, description="Rechercher par titre"),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    """
    Liste tous les documents indexés avec pagination.

    - **page**: Numéro de page (défaut: 1)
    - **limit**: Documents par page (défaut: 20, max: 100)
    - **status**: Filtrer par statut (pending, indexed, error)
    - **search**: Rechercher dans les titres
    """
    query = db.query(Document)

    # Filtres
    if status:
        query = query.filter(Document.status == status)
    if search:
        query = query.filter(Document.title.ilike(f"%{search}%"))

    # Compte total
    total = query.count()

    # Pagination
    offset = (page - 1) * limit
    documents = query.order_by(Document.created_at.desc()).offset(offset).limit(limit).all()

    # Conversion en schema
    doc_infos = [
        DocumentInfo(
            id=doc.id,
            title=doc.title,
            authors=doc.authors,
            year=doc.publication_year,
            page_count=doc.page_count,
            chunk_count=len(doc.chunks),
            status=doc.status,
            indexed_at=doc.indexed_at,
        )
        for doc in documents
    ]

    return DocumentListResponse(
        documents=doc_infos,
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentInfo:
    """
    Récupère les détails d'un document.

    - **document_id**: ID du document
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    return DocumentInfo(
        id=document.id,
        title=document.title,
        authors=document.authors,
        year=document.publication_year,
        page_count=document.page_count,
        chunk_count=len(document.chunks),
        status=document.status,
        indexed_at=document.indexed_at,
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
):
    """
    Supprime un document et tous ses chunks.

    - **document_id**: ID du document à supprimer
    """
    deleted = indexing_service.delete_document(db, document_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    return {"status": "deleted", "document_id": document_id}

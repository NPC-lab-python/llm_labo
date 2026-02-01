"""Routes pour la gestion des documents."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.database import get_db, Document
from app.models.schemas import DocumentInfo, DocumentListResponse, MetadataQualityStats
from app.services.indexing_service import indexing_service
from app.core.metadata_analyzer import metadata_analyzer

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


@router.get("/stats", response_model=MetadataQualityStats)
async def get_stats(
    db: Session = Depends(get_db),
) -> MetadataQualityStats:
    """
    Alias simplifié pour les statistiques (utilisé par le frontend).
    """
    return await get_metadata_quality_stats(recalculate=False, db=db)


# IMPORTANT: Cette route doit être AVANT /documents/{document_id}
# sinon "metadata" serait interprété comme un document_id
@router.get("/documents/metadata/quality", response_model=MetadataQualityStats)
async def get_metadata_quality_stats(
    recalculate: bool = Query(default=False, description="Recalculer les scores"),
    db: Session = Depends(get_db),
) -> MetadataQualityStats:
    """
    Retourne les statistiques de qualité des métadonnées.

    - **recalculate**: Recalculer les scores pour tous les documents
    """
    documents = db.query(Document).filter(Document.status == "indexed").all()

    if not documents:
        return MetadataQualityStats(
            total_documents=0,
            average_score=0.0,
            score_distribution={"excellent": 0, "good": 0, "fair": 0, "poor": 0},
            missing_fields={"title": 0, "authors": 0, "year": 0},
            low_quality_count=0,
            documents_needing_review=[],
        )

    # Calcul ou récupération des scores
    scores = []
    missing_title = 0
    missing_authors = 0
    missing_year = 0
    low_quality_docs = []

    for doc in documents:
        if recalculate or doc.metadata_quality_score == 0.0:
            # Recalculer le score
            report = metadata_analyzer.analyze(
                title=doc.title,
                authors=doc.authors,
                year=doc.publication_year,
                abstract=doc.abstract,
                keywords=doc.keywords,
            )
            score = report.score

            # Mettre à jour en base
            doc.metadata_quality_score = score
            db.add(doc)
        else:
            score = doc.metadata_quality_score

        scores.append(score)

        # Comptage des champs manquants
        if not doc.title or doc.title.strip() == "":
            missing_title += 1
        if not doc.authors or doc.authors.strip() == "":
            missing_authors += 1
        if doc.publication_year is None:
            missing_year += 1

        # Documents à corriger (score < 0.5)
        if score < 0.5:
            low_quality_docs.append({
                "id": doc.id,
                "title": doc.title[:80] if doc.title else "Sans titre",
                "score": round(score, 3),
                "missing": [
                    f for f in ["title", "authors", "year"]
                    if (f == "title" and (not doc.title or doc.title.strip() == ""))
                    or (f == "authors" and (not doc.authors or doc.authors.strip() == ""))
                    or (f == "year" and doc.publication_year is None)
                ],
            })

    if recalculate:
        db.commit()

    # Distribution des scores
    excellent = sum(1 for s in scores if s >= 0.8)
    good = sum(1 for s in scores if 0.6 <= s < 0.8)
    fair = sum(1 for s in scores if 0.4 <= s < 0.6)
    poor = sum(1 for s in scores if s < 0.4)

    # Trier les documents à corriger par score croissant
    low_quality_docs.sort(key=lambda x: x["score"])

    return MetadataQualityStats(
        total_documents=len(documents),
        average_score=round(sum(scores) / len(scores), 3) if scores else 0.0,
        score_distribution={
            "excellent": excellent,
            "good": good,
            "fair": fair,
            "poor": poor,
        },
        missing_fields={
            "title": missing_title,
            "authors": missing_authors,
            "year": missing_year,
        },
        low_quality_count=len(low_quality_docs),
        documents_needing_review=low_quality_docs[:20],  # Top 20 à corriger
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


@router.get("/documents/{document_id}/pdf")
async def get_document_pdf(
    document_id: str,
    page: int | None = Query(default=None, description="Numéro de page (pour l'ancre)"),
    db: Session = Depends(get_db),
):
    """
    Récupère le fichier PDF d'un document.

    - **document_id**: ID du document
    - **page**: Numéro de page optionnel (pour l'ancre dans le viewer PDF)
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    pdf_path = Path(document.file_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="Fichier PDF introuvable")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=pdf_path.name,
    )

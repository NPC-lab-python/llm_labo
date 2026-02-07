"""Routes pour la gestion des projets de recherche."""

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.models.database import get_db, Project, ProjectSource, ProjectSection, Document
from app.models.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectInfo,
    ProjectDetail,
    ProjectListResponse,
    ProjectSourceCreate,
    ProjectSourceUpdate,
    ProjectSourceInfo,
    ProjectSectionCreate,
    ProjectSectionUpdate,
    ProjectSectionInfo,
    ExportRequest,
    ExportResponse,
)
from app.services.export_service import export_service

router = APIRouter()


# === CRUD Projets ===


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects(
    status: str | None = Query(default=None, description="Filtrer par statut"),
    db: Session = Depends(get_db),
) -> ProjectListResponse:
    """Liste tous les projets."""
    query = db.query(Project)

    if status:
        query = query.filter(Project.status == status)

    projects = query.order_by(Project.updated_at.desc()).all()

    project_infos = []
    for project in projects:
        project_infos.append(
            ProjectInfo(
                id=project.id,
                title=project.title,
                description=project.description,
                status=project.status,
                sources_count=len(project.sources),
                sections_count=len(project.sections),
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
        )

    return ProjectListResponse(projects=project_infos, total=len(project_infos))


@router.post("/projects", response_model=ProjectInfo)
async def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectInfo:
    """Crée un nouveau projet."""
    project = Project(
        id=str(uuid.uuid4()),
        title=data.title,
        description=data.description,
        status="draft",
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return ProjectInfo(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status,
        sources_count=0,
        sections_count=0,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/projects/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectDetail:
    """Récupère les détails d'un projet."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    # Construire les infos des sources
    sources_info = []
    for source in project.sources:
        doc = source.document
        highlights = json.loads(source.highlights) if source.highlights else []
        sources_info.append(
            ProjectSourceInfo(
                id=source.id,
                document_id=source.document_id,
                document_title=doc.title if doc else "Document supprimé",
                document_authors=doc.authors if doc else None,
                document_year=doc.publication_year if doc else None,
                notes=source.notes,
                highlights=highlights,
                relevance=source.relevance,
                added_at=source.added_at,
            )
        )

    # Construire les infos des sections
    sections_info = []
    for section in sorted(project.sections, key=lambda s: s.section_order):
        cited = json.loads(section.cited_sources) if section.cited_sources else []
        sections_info.append(
            ProjectSectionInfo(
                id=section.id,
                section_type=section.section_type,
                section_order=section.section_order,
                title=section.title,
                content=section.content,
                cited_sources=cited,
                word_count=section.word_count,
                status=section.status,
                updated_at=section.updated_at,
            )
        )

    return ProjectDetail(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status,
        sources=sources_info,
        sections=sections_info,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.put("/projects/{project_id}", response_model=ProjectInfo)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectInfo:
    """Met à jour un projet."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    if data.title is not None:
        project.title = data.title
    if data.description is not None:
        project.description = data.description
    if data.status is not None:
        project.status = data.status

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)

    return ProjectInfo(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status,
        sources_count=len(project.sources),
        sections_count=len(project.sections),
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Supprime un projet."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    db.delete(project)
    db.commit()

    return {"status": "deleted", "project_id": project_id}


# === Sources de projet ===


@router.post("/projects/{project_id}/sources", response_model=ProjectSourceInfo)
async def add_source_to_project(
    project_id: str,
    data: ProjectSourceCreate,
    db: Session = Depends(get_db),
) -> ProjectSourceInfo:
    """Ajoute une source à un projet."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    document = db.query(Document).filter(Document.id == data.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")

    # Vérifier si la source existe déjà
    existing = db.query(ProjectSource).filter(
        ProjectSource.project_id == project_id,
        ProjectSource.document_id == data.document_id,
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Cette source est déjà dans le projet")

    source = ProjectSource(
        id=str(uuid.uuid4()),
        project_id=project_id,
        document_id=data.document_id,
        notes=data.notes,
        relevance=data.relevance,
    )

    db.add(source)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(source)

    return ProjectSourceInfo(
        id=source.id,
        document_id=source.document_id,
        document_title=document.title,
        document_authors=document.authors,
        document_year=document.publication_year,
        notes=source.notes,
        highlights=[],
        relevance=source.relevance,
        added_at=source.added_at,
    )


@router.put("/projects/{project_id}/sources/{source_id}", response_model=ProjectSourceInfo)
async def update_project_source(
    project_id: str,
    source_id: str,
    data: ProjectSourceUpdate,
    db: Session = Depends(get_db),
) -> ProjectSourceInfo:
    """Met à jour une source de projet."""
    source = db.query(ProjectSource).filter(
        ProjectSource.id == source_id,
        ProjectSource.project_id == project_id,
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")

    if data.notes is not None:
        source.notes = data.notes
    if data.highlights is not None:
        source.highlights = json.dumps(data.highlights)
    if data.relevance is not None:
        source.relevance = data.relevance

    # Mettre à jour le projet
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(source)

    document = source.document
    highlights = json.loads(source.highlights) if source.highlights else []

    return ProjectSourceInfo(
        id=source.id,
        document_id=source.document_id,
        document_title=document.title if document else "Document supprimé",
        document_authors=document.authors if document else None,
        document_year=document.publication_year if document else None,
        notes=source.notes,
        highlights=highlights,
        relevance=source.relevance,
        added_at=source.added_at,
    )


@router.delete("/projects/{project_id}/sources/{source_id}")
async def remove_source_from_project(
    project_id: str,
    source_id: str,
    db: Session = Depends(get_db),
):
    """Retire une source d'un projet."""
    source = db.query(ProjectSource).filter(
        ProjectSource.id == source_id,
        ProjectSource.project_id == project_id,
    ).first()

    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")

    db.delete(source)

    # Mettre à jour le projet
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()

    db.commit()

    return {"status": "removed", "source_id": source_id}


# === Sections de projet ===


@router.post("/projects/{project_id}/sections", response_model=ProjectSectionInfo)
async def create_section(
    project_id: str,
    data: ProjectSectionCreate,
    db: Session = Depends(get_db),
) -> ProjectSectionInfo:
    """Crée une section dans un projet."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    # Déterminer l'ordre de la section
    existing_sections = db.query(ProjectSection).filter(
        ProjectSection.project_id == project_id
    ).count()

    word_count = len(data.content.split()) if data.content else 0

    section = ProjectSection(
        id=str(uuid.uuid4()),
        project_id=project_id,
        section_type=data.section_type,
        section_order=existing_sections,
        title=data.title,
        content=data.content,
        word_count=word_count,
    )

    db.add(section)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(section)

    return ProjectSectionInfo(
        id=section.id,
        section_type=section.section_type,
        section_order=section.section_order,
        title=section.title,
        content=section.content,
        cited_sources=[],
        word_count=section.word_count,
        status=section.status,
        updated_at=section.updated_at,
    )


@router.put("/projects/{project_id}/sections/{section_id}", response_model=ProjectSectionInfo)
async def update_section(
    project_id: str,
    section_id: str,
    data: ProjectSectionUpdate,
    db: Session = Depends(get_db),
) -> ProjectSectionInfo:
    """Met à jour une section."""
    section = db.query(ProjectSection).filter(
        ProjectSection.id == section_id,
        ProjectSection.project_id == project_id,
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section non trouvée")

    if data.title is not None:
        section.title = data.title
    if data.content is not None:
        section.content = data.content
        section.word_count = len(data.content.split()) if data.content else 0
    if data.section_order is not None:
        section.section_order = data.section_order
    if data.status is not None:
        section.status = data.status

    section.updated_at = datetime.utcnow()

    # Mettre à jour le projet
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(section)

    cited = json.loads(section.cited_sources) if section.cited_sources else []

    return ProjectSectionInfo(
        id=section.id,
        section_type=section.section_type,
        section_order=section.section_order,
        title=section.title,
        content=section.content,
        cited_sources=cited,
        word_count=section.word_count,
        status=section.status,
        updated_at=section.updated_at,
    )


@router.delete("/projects/{project_id}/sections/{section_id}")
async def delete_section(
    project_id: str,
    section_id: str,
    db: Session = Depends(get_db),
):
    """Supprime une section."""
    section = db.query(ProjectSection).filter(
        ProjectSection.id == section_id,
        ProjectSection.project_id == project_id,
    ).first()

    if not section:
        raise HTTPException(status_code=404, detail="Section non trouvée")

    db.delete(section)

    # Mettre à jour le projet
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.updated_at = datetime.utcnow()

    db.commit()

    return {"status": "deleted", "section_id": section_id}


# === Export ===


@router.post("/projects/{project_id}/export")
async def export_project(
    project_id: str,
    data: ExportRequest,
    db: Session = Depends(get_db),
):
    """Exporte un projet au format demandé."""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")

    try:
        file_path = export_service.export_project(
            db=db,
            project=project,
            format=data.format,
            include_bibliography=data.include_bibliography,
            citation_style=data.citation_style,
        )

        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if data.format == "docx" else "text/markdown",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'export: {e}")

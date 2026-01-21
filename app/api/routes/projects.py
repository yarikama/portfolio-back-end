from typing import Optional
from uuid import UUID

from db.dependency import get_db
from db.models.projects import Project
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/projects")
async def get_projects(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(Project)

    if category:
        query = query.filter(Project.category == category)
    if featured is not None:
        query = query.filter(Project.featured == featured)
    if tag:
        query = query.filter(Project.tags.contains([tag]))

    total = query.count()
    projects = query.offset(offset).limit(limit).all()

    return {
        "data": [ProjectResponse.model_validate(p) for p in projects],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "hasMore": offset + limit < total,
        },
    }


@router.get("/projects/{slug}")
async def get_project(
    slug: str = Path(..., min_length=1, max_length=255),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"data": ProjectResponse.model_validate(project)}


@router.post("/projects", status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
):
    is_exists = db.query(Project).filter(Project.slug == project_in.slug).first()
    if is_exists:
        raise HTTPException(status_code=400, detail="Project already exists")

    project = Project(**project_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"data": ProjectResponse.model_validate(project)}


@router.put("/projects/{id}")
async def update_project(
    id: UUID,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
):
    db_project = db.query(Project).filter(Project.id == id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    for field, value in project_in.model_dump(exclude_unset=True).items():
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)
    return {"data": ProjectResponse.model_validate(db_project)}


@router.delete("/projects/{id}", status_code=204)
async def delete_project(
    id: UUID,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None

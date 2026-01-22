from typing import Optional
from uuid import UUID

from api.dependencies import CurrentAdmin
from core.paginator import offset_pagination
from db.dependency import get_db
from db.models.projects import Project
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from schemas.projects import (
    ProjectCreate,
    ProjectReorderRequest,
    ProjectResponse,
    ProjectUpdate,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter()

# ============================================================================
# Admin Routes (require authentication)
# ============================================================================


@router.get("/admin/projects")
async def get_all_projects_admin(
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Admin endpoint: Get all projects including unpublished."""
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
        "pagination": offset_pagination(offset, limit, total),
    }


@router.post("/admin/projects", status_code=201)
async def create_project(
    project_in: ProjectCreate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Create a new project."""
    is_exists = db.query(Project).filter(Project.slug == project_in.slug).first()
    if is_exists:
        raise HTTPException(
            status_code=409,
            detail=f"Project with slug '{project_in.slug}' already exists",
        )

    project = Project(**project_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"data": ProjectResponse.model_validate(project)}


@router.put("/admin/projects/{id}")
async def update_project(
    id: UUID,
    project_in: ProjectUpdate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Update a project."""
    db_project = db.query(Project).filter(Project.id == id).first()
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    update_data = project_in.model_dump(exclude_unset=True)

    # Check if slug is being updated and if it conflicts with existing records
    if "slug" in update_data:
        existing = (
            db.query(Project)
            .filter(Project.slug == update_data["slug"], Project.id != id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Project with slug '{update_data['slug']}' already exists",
            )

    for field, value in update_data.items():
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)
    return {"data": ProjectResponse.model_validate(db_project)}


@router.delete("/admin/projects/{id}", status_code=204)
async def delete_project(
    id: UUID,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Delete a project."""
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None


@router.patch("/admin/projects/reorder")
async def reorder_projects(
    request: ProjectReorderRequest,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Reorder projects."""
    updated_count = 0
    for item in request.orders:
        updated_count += (
            db.query(Project)
            .filter(Project.id == item.id)
            .update({"order": item.order})
        )
    db.commit()
    return {
        "data": {"message": "Projects reordered successfully", "updated": updated_count}
    }


# ============================================================================
# Public Routes (no authentication required)
# ============================================================================


@router.get("/projects")
async def get_projects(
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    featured: Optional[bool] = Query(None),
    tag: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Public endpoint: Get only published projects."""
    query = db.query(Project).filter(Project.published)

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
        "pagination": offset_pagination(offset, limit, total),
    }


@router.get("/projects/categories")
async def get_project_categories(
    db: Session = Depends(get_db),
):
    """Public endpoint: Get project categories with counts."""
    total = db.query(Project.category).filter(Project.published).count()

    category_counts = (
        db.query(Project.category, func.count(Project.id).label("count"))
        .filter(Project.published)
        .group_by(Project.category)
        .all()
    )

    categories = [{"id": "all", "label": "All", "count": total}]

    label_map = {
        "engineering": "Engineering",
        "ml": "ML/AI",
    }

    categories += [
        {"id": category, "label": label_map.get(category, category), "count": count}
        for category, count in category_counts
    ]
    return {"data": categories}


@router.get("/projects/{slug}")
async def get_project(
    slug: str = Path(..., min_length=1, max_length=255),
    db: Session = Depends(get_db),
):
    """Public endpoint: Get a single project by slug."""
    project = db.query(Project).filter(Project.slug == slug).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"data": ProjectResponse.model_validate(project)}

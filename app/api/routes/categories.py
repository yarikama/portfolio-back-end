"""Category CRUD routes."""

from typing import Optional
from uuid import UUID

from api.dependencies import CurrentAdmin
from db.dependency import get_db
from db.models.category import Category
from db.models.projects import Project
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.category import (
    CategoryCreate,
    CategoryReorderRequest,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithCount,
)
from sqlalchemy.orm import Session

router = APIRouter()

# ============================================================================
# Admin Routes (require authentication)
# ============================================================================


@router.get("/admin/categories")
async def get_all_categories_admin(
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Get all categories."""
    categories = db.query(Category).order_by(Category.order, Category.label).all()
    return {"data": [CategoryResponse.model_validate(c) for c in categories]}


@router.post("/admin/categories", status_code=201)
async def create_category(
    category: CategoryCreate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Create a new category."""
    # Check if name already exists
    existing = db.query(Category).filter(Category.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Category with name '{category.name}' already exists",
        )

    db_category = Category(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return {"data": CategoryResponse.model_validate(db_category)}


@router.put("/admin/categories/{id}")
async def update_category(
    id: UUID,
    category: CategoryUpdate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Update a category."""
    db_category = db.query(Category).filter(Category.id == id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = category.model_dump(exclude_unset=True)

    # Check if name is being updated and if it conflicts
    if "name" in update_data:
        existing = (
            db.query(Category)
            .filter(Category.name == update_data["name"], Category.id != id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Category with name '{update_data['name']}' already exists",
            )

    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return {"data": CategoryResponse.model_validate(db_category)}


@router.delete("/admin/categories/{id}", status_code=204)
async def delete_category(
    id: UUID,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Delete a category."""
    db_category = db.query(Category).filter(Category.id == id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if category has projects
    project_count = db.query(Project).filter(Project.category_id == id).count()
    if project_count > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot delete category with {project_count} project(s). "
                "Please reassign or delete projects first."
            ),
        )

    db.delete(db_category)
    db.commit()
    return None


@router.patch("/admin/categories/reorder")
async def reorder_categories(
    request: CategoryReorderRequest,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    """Admin endpoint: Reorder categories."""
    updated_count = 0
    for item in request.orders:
        updated_count += (
            db.query(Category)
            .filter(Category.id == item.id)
            .update({"order": item.order})
        )
    db.commit()
    return {
        "data": {
            "message": "Categories reordered successfully",
            "updated": updated_count,
        }
    }


# ============================================================================
# Public Routes (no authentication required)
# ============================================================================


@router.get("/categories")
async def get_categories(
    db: Session = Depends(get_db),
    include_counts: Optional[bool] = Query(False, description="Include project counts"),
):
    """Public endpoint: Get all categories, optionally with project counts."""
    categories = db.query(Category).order_by(Category.order, Category.label).all()

    if not include_counts:
        return {"data": [CategoryResponse.model_validate(c) for c in categories]}

    # Get project counts for each category (only published projects)
    result = []
    for category in categories:
        count = (
            db.query(Project)
            .filter(Project.category_id == category.id, Project.published)
            .count()
        )
        category_dict = CategoryResponse.model_validate(category).model_dump()
        category_dict["count"] = count
        result.append(CategoryWithCount(**category_dict))

    # Add "All" category
    total = db.query(Project).filter(Project.published).count()
    all_category = {
        "id": "00000000-0000-0000-0000-000000000000",  # Special UUID for "All"
        "name": "all",
        "label": "All",
        "description": "All projects",
        "order": -1,
        "count": total,
        "created_at": categories[0].created_at if categories else None,
        "updated_at": categories[0].updated_at if categories else None,
    }

    return {"data": [CategoryWithCount(**all_category)] + result}


@router.get("/categories/{id}")
async def get_category(
    id: UUID,
    db: Session = Depends(get_db),
):
    """Public endpoint: Get a single category by ID."""
    category = db.query(Category).filter(Category.id == id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"data": CategoryResponse.model_validate(category)}

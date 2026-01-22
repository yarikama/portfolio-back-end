from typing import Optional
from uuid import UUID

from api.dependencies import CurrentAdmin
from core.paginator import offset_pagination
from db.dependency import get_db
from db.models.lab_notes import LabNote
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from schemas.lab_notes import (
    LabNoteCreate,
    LabNoteListResponse,
    LabNoteResponse,
    LabNoteUpdate,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/lab-notes")
async def get_lab_notes(
    db: Session = Depends(get_db),
    tag: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(LabNote).filter(LabNote.published)

    if tag:
        query = query.filter(LabNote.tags.contains([tag]))

    total = query.count()
    lab_notes = query.order_by(LabNote.date.desc()).offset(offset).limit(limit).all()

    return {
        "data": [LabNoteListResponse.model_validate(ln) for ln in lab_notes],
        "pagination": offset_pagination(offset, limit, total),
    }


@router.get("/lab-notes/tags")
async def get_lab_notes_tags(
    db: Session = Depends(get_db),
):
    result = (
        db.query(
            func.unnest(LabNote.tags).label("tag"),
        )
        .filter(LabNote.published)
        .subquery()
    )

    tags = (
        db.query(result.c.tag, func.count(result.c.tag).label("count"))
        .group_by(result.c.tag)
        .order_by(func.count(result.c.tag).desc())
        .all()
    )

    return {"data": [{"tag": tag, "count": count} for tag, count in tags]}


@router.get("/lab-notes/{slug}")
async def get_lab_note(
    db: Session = Depends(get_db),
    slug: str = Path(..., min_length=1, max_length=255),
):
    lab_note = db.query(LabNote).filter(LabNote.slug == slug).first()
    if not lab_note:
        raise HTTPException(status_code=404, detail="Lab note not found")
    return {"data": LabNoteResponse.model_validate(lab_note)}


@router.post("/lab-notes", status_code=201)
async def create_lab_note(
    lab_note: LabNoteCreate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    db_lab_note = LabNote(**lab_note.model_dump())
    db.add(db_lab_note)
    db.commit()
    db.refresh(db_lab_note)
    return {"data": LabNoteResponse.model_validate(db_lab_note)}


@router.put("/lab-notes/{id}")
async def update_lab_note(
    lab_note: LabNoteUpdate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
    id: UUID = Path(...),
):
    db_lab_note = db.query(LabNote).filter(LabNote.id == id).first()
    if not db_lab_note:
        raise HTTPException(status_code=404, detail="Lab note not found")

    update_data = lab_note.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_lab_note, field, value)

    db.commit()
    db.refresh(db_lab_note)
    return {"data": LabNoteResponse.model_validate(db_lab_note)}


@router.delete("/lab-notes/{id}", status_code=204)
async def delete_lab_note(
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
    id: UUID = Path(...),
):
    db_lab_note = db.query(LabNote).filter(LabNote.id == id).first()
    if not db_lab_note:
        raise HTTPException(status_code=404, detail="Lab note not found")

    db.delete(db_lab_note)
    db.commit()
    return None

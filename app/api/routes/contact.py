from typing import Optional
from uuid import UUID

from api.dependencies import CurrentAdmin
from core.paginator import offset_pagination
from db.dependency import get_db
from db.models.contact import ContactMessage
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from schemas.contact import ContactCreate, ContactResponse, ContactUpdate
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/contact", status_code=201)
async def create_contact(
    contact: ContactCreate,
    db: Session = Depends(get_db),
):
    db_contact = ContactMessage(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return {
        "data": {
            "id": str(db_contact.id),
            "message": "Thank you for your message. I'll get back to you soon!",
        }
    }


@router.get("/contact", status_code=200)
async def get_contacts(
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
    read: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    query = db.query(ContactMessage)
    if read is not None:
        query = query.filter(ContactMessage.read == read)
    total = query.count()
    contacts = (
        query.order_by(ContactMessage.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "data": [ContactResponse.model_validate(c) for c in contacts],
        "pagination": offset_pagination(offset, limit, total),
    }


@router.patch("/contact/{id}")
async def update_contact(
    contact_update: ContactUpdate,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
    id: UUID = Path(...),
):
    db_contact = db.query(ContactMessage).filter(ContactMessage.id == id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact message not found")

    for field, value in contact_update.model_dump(exclude_unset=True).items():
        setattr(db_contact, field, value)

    db.commit()
    db.refresh(db_contact)
    return {"data": ContactResponse.model_validate(db_contact)}


@router.delete("/contact/{id}", status_code=204)
async def delete_contact(
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
    id: UUID = Path(...),
):
    db_contact = db.query(ContactMessage).filter(ContactMessage.id == id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact message not found")

    db.delete(db_contact)
    db.commit()
    return None

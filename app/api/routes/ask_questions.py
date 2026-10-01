"""The chat's questions in the admin area: what visitors asked, and the
owner's ratings of the answers (services/ask_log.py stores them)."""

from typing import Literal
from uuid import UUID

from api.dependencies import CurrentAdmin
from core.paginator import offset_pagination
from db.dependency import get_db
from db.models.ask import AskQuestion
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.ask_questions import AskQuestionRating, AskQuestionResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/admin/ask/questions")
async def list_questions(
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
    who: Literal["visitors", "admin", "all"] = Query("visitors"),
    uncited: bool = Query(False, description="Only answers that cite nothing"),
    passage: bool = Query(False, description="Only questions about a passage"),
    failed: bool = Query(False, description="Only answers cut off or broken off"),
    rating: Literal["good", "bad", "none"] | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Newest first."""
    query = db.query(AskQuestion)
    if who != "all":
        query = query.filter(AskQuestion.admin.is_(who == "admin"))
    if uncited:
        query = query.filter(func.jsonb_array_length(AskQuestion.citations) == 0)
    if passage:
        query = query.filter(AskQuestion.quote.isnot(None))
    if failed:
        query = query.filter(
            (AskQuestion.status != "answered") | AskQuestion.truncated.is_(True)
        )
    if rating == "none":
        query = query.filter(AskQuestion.rating.is_(None))
    elif rating:
        query = query.filter(AskQuestion.rating == rating)

    total = query.count()
    rows = (
        query.order_by(AskQuestion.created_at.desc(), AskQuestion.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "data": [
            AskQuestionResponse.model_validate(row).model_dump(
                by_alias=True, mode="json"
            )
            for row in rows
        ],
        "pagination": offset_pagination(offset, limit, total),
    }


@router.patch("/admin/ask/questions/{id}")
async def rate_question(
    id: UUID,
    body: AskQuestionRating,
    _admin: CurrentAdmin,
    db: Session = Depends(get_db),
):
    row = db.get(AskQuestion, id)
    if row is None:
        raise HTTPException(status_code=404, detail="Question not found")
    row.rating = body.rating
    db.commit()
    db.refresh(row)
    return {
        "data": AskQuestionResponse.model_validate(row).model_dump(
            by_alias=True, mode="json"
        )
    }

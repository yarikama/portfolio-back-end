"""The chat's questions in the admin area: what visitors asked, the owner's
ratings of the answers (services/ask_log.py stores them), and how many
visitors asked since each admin last looked."""

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from api.dependencies import CurrentAdmin
from core.paginator import offset_pagination
from db.dependency import get_db
from db.models.admin_seen import AdminSeen
from db.models.ask import AskQuestion
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.ask_questions import (
    AskQuestionRating,
    AskQuestionResponse,
    NewQuestions,
    SeenQuestions,
)
from sqlalchemy import func
from sqlalchemy.orm import Session

router = APIRouter()

PAGE = "questions"


def last_seen(db: Session, admin: str) -> datetime | None:
    row = db.get(AdminSeen, (admin, PAGE))
    return row.seen_at if row else None


@router.get("/admin/ask/questions/new")
async def new_questions(admin: CurrentAdmin, db: Session = Depends(get_db)):
    """How many visitors asked since this admin last opened Questions."""
    since = last_seen(db, admin)
    query = db.query(AskQuestion).filter(AskQuestion.admin.is_(False))
    if since is not None:
        query = query.filter(AskQuestion.created_at > since)
    return {
        "data": NewQuestions(count=query.count(), since=since).model_dump(
            by_alias=True, mode="json"
        )
    }


@router.post("/admin/ask/questions/seen")
async def mark_questions_seen(admin: CurrentAdmin, db: Session = Depends(get_db)):
    """Opening Questions: what came in after the time returned is new."""
    row = db.get(AdminSeen, (admin, PAGE))
    previous = row.seen_at if row else None
    now = datetime.now(timezone.utc)
    if row is None:
        db.add(AdminSeen(email=admin, page=PAGE, seen_at=now))
    else:
        row.seen_at = now
    db.commit()
    return {
        "data": SeenQuestions(previous=previous).model_dump(by_alias=True, mode="json")
    }


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

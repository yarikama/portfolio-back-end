"""
The admin's to-dos: each day's daily items, added the first time that day's
list is asked for, plus whatever the owner adds. Not done, an item carries
over to the following days.
"""

from dataclasses import dataclass
from datetime import date

from db.models.todo import AdminTodo
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class Daily:
    key: str
    text: str
    href: str


DAILY = [Daily("neetcode", "Solve a problem on NeetCode", "https://neetcode.io")]


def add_daily(db: Session, day: date) -> None:
    """The day's daily items, once: one removed that day stays removed."""
    have = {
        key
        for (key,) in db.query(AdminTodo.daily_key).filter(
            AdminTodo.day == day, AdminTodo.daily_key.isnot(None)
        )
    }
    for daily in DAILY:
        if daily.key in have:
            continue
        db.add(
            AdminTodo(text=daily.text, href=daily.href, day=day, daily_key=daily.key)
        )
        try:
            db.commit()
        except IntegrityError:
            # Another request added it first.
            db.rollback()


def for_day(db: Session, day: date) -> list[AdminTodo]:
    """Everything still open up to `day`, and what was done on it: the
    oldest first, so what carried over leads."""
    add_daily(db, day)
    return (
        db.query(AdminTodo)
        .filter(
            AdminTodo.removed.is_(False),
            AdminTodo.day <= day,
            or_(AdminTodo.done_on.is_(None), AdminTodo.done_on == day),
        )
        .order_by(AdminTodo.day, AdminTodo.created_at)
        .all()
    )


def history(db: Session, limit: int) -> list[str]:
    """What the owner has written as to-dos, most recent first and each
    once, for completing a new one as it is typed. Daily items and removed
    ones are left out."""
    latest = func.max(AdminTodo.created_at)
    rows = (
        db.query(AdminTodo.text, latest)
        .filter(AdminTodo.daily_key.is_(None), AdminTodo.removed.is_(False))
        .group_by(AdminTodo.text)
        .order_by(latest.desc())
        .limit(limit)
        .all()
    )
    return [text for text, _ in rows]

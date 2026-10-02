"""The admin's to-dos, on the welcome page (services/todos.py)."""

from datetime import date
from uuid import UUID

from api.dependencies import CurrentAdmin
from db.dependency import get_db
from db.models.todo import AdminTodo
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from schemas.todos import TodoCreate, TodoResponse, TodoUpdate
from services import todos
from sqlalchemy.orm import Session

router = APIRouter()


def dump(row: AdminTodo) -> dict:
    return TodoResponse.model_validate(row).model_dump(by_alias=True, mode="json")


def find(db: Session, id: UUID) -> AdminTodo:
    row = db.get(AdminTodo, id)
    if row is None or row.removed:
        raise HTTPException(status_code=404, detail="To-do not found")
    return row


@router.get("/admin/todos")
async def list_todos(
    _admin: CurrentAdmin,
    day: date = Query(..., description="The owner's today, in their local time"),
    db: Session = Depends(get_db),
):
    return {"data": [dump(row) for row in todos.for_day(db, day)]}


@router.post("/admin/todos", status_code=status.HTTP_201_CREATED)
async def add_todo(
    body: TodoCreate, _admin: CurrentAdmin, db: Session = Depends(get_db)
):
    row = AdminTodo(text=body.text, href=body.href, day=body.day)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": dump(row)}


@router.patch("/admin/todos/{id}")
async def tick_todo(
    id: UUID, body: TodoUpdate, _admin: CurrentAdmin, db: Session = Depends(get_db)
):
    row = find(db, id)
    row.done_on = body.day if body.done else None
    db.commit()
    db.refresh(row)
    return {"data": dump(row)}


@router.delete("/admin/todos/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_todo(id: UUID, _admin: CurrentAdmin, db: Session = Depends(get_db)):
    # Hidden, not deleted: a daily item would otherwise come back that day.
    find(db, id).removed = True
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

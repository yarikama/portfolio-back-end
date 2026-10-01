import os
from datetime import datetime, timedelta, timezone

import pytest
from core import config
from core.security import create_access_token
from db.dependency import get_db
from db.models.ask import AskQuestion
from db.session import Base
from fastapi.testclient import TestClient
from main import get_application
from services import ask_log
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PREFIX = "test-ask-log: "


@pytest.fixture
def factory(monkeypatch):
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db"
    )
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    monkeypatch.setattr(ask_log, "SessionLocal", factory)
    yield factory
    with factory() as db:
        db.query(AskQuestion).filter(AskQuestion.question.startswith(PREFIX)).delete(
            synchronize_session=False
        )
        db.commit()


def entry(question, **change):
    fields = dict(
        question=PREFIX + question,
        quote=None,
        page=None,
        answer="An answer.",
        citations=[{"id": "P1", "kind": "project", "title": "PAPIT", "url": None}],
        status="answered",
        truncated=False,
        output_tokens=3,
        duration_ms=1200,
        admin=False,
    )
    return ask_log.Entry(**{**fields, **change})


@pytest.fixture
def client(factory):
    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app = get_application()
    app.dependency_overrides[get_db] = override_get_db
    token = create_access_token({"sub": config.ADMIN_USERNAME}, str(config.SECRET_KEY))
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


def questions(client, **params):
    response = client.get("/api/v1/admin/ask/questions", params=params)
    assert response.status_code == 200
    return [
        q["question"].removeprefix(PREFIX)
        for q in response.json()["data"]
        if q["question"].startswith(PREFIX)
    ]


def test_a_question_is_stored_and_old_ones_are_forgotten(factory):
    now = datetime.now(timezone.utc)
    days = config.ASK_QUESTION_RETENTION_DAYS
    ask_log.record(entry("old", created_at=now - timedelta(days=days, minutes=1)))
    ask_log.record(entry("kept", created_at=now - timedelta(days=days - 1)))
    ask_log.record(entry("new", created_at=now))

    with factory() as db:
        rows = db.query(AskQuestion).filter(AskQuestion.question.startswith(PREFIX))
        assert sorted(r.question.removeprefix(PREFIX) for r in rows) == ["kept", "new"]


def test_a_database_problem_does_not_raise(monkeypatch):
    def broken():
        raise RuntimeError("database down")

    monkeypatch.setattr(ask_log, "SessionLocal", broken)
    ask_log.record(entry("lost"))  # logged, not raised


def test_the_admin_lists_questions_newest_first_with_filters(client):
    now = datetime.now(timezone.utc)
    rows = [
        entry("visitor", created_at=now - timedelta(minutes=5)),
        entry("owner", admin=True, created_at=now - timedelta(minutes=4)),
        entry("uncited", citations=[], created_at=now - timedelta(minutes=3)),
        entry(
            "passage",
            quote="A passage.",
            page="/notes/x",
            created_at=now - timedelta(minutes=2),
        ),
        entry("cut", truncated=True, created_at=now - timedelta(minutes=1)),
        entry("broke", status="error", citations=[], created_at=now),
    ]
    for row in rows:
        ask_log.record(row)

    assert questions(client) == ["broke", "cut", "passage", "uncited", "visitor"]
    assert questions(client, who="admin") == ["owner"]
    assert len(questions(client, who="all")) == 6
    assert questions(client, uncited=True) == ["broke", "uncited"]
    assert questions(client, passage=True) == ["passage"]
    assert questions(client, failed=True) == ["broke", "cut"]


def test_the_admin_rates_an_answer(client):
    ask_log.record(entry("rate me"))
    [row] = [
        q
        for q in client.get("/api/v1/admin/ask/questions").json()["data"]
        if q["question"] == PREFIX + "rate me"
    ]
    assert row["rating"] is None and row["durationMs"] == 1200

    url = f"/api/v1/admin/ask/questions/{row['id']}"
    assert client.patch(url, json={"rating": "bad"}).json()["data"]["rating"] == "bad"
    assert questions(client, rating="bad") == ["rate me"]
    assert client.patch(url, json={"rating": None}).json()["data"]["rating"] is None
    assert questions(client, rating="none") == ["rate me"]
    assert client.patch(url, json={"rating": "meh"}).status_code == 422


def test_only_the_admin_reads_them(client):
    client.headers.pop("Authorization")
    assert client.get("/api/v1/admin/ask/questions").status_code == 401
    missing = "/api/v1/admin/ask/questions/00000000-0000-0000-0000-000000000000"
    assert client.patch(missing, json={"rating": "good"}).status_code == 401

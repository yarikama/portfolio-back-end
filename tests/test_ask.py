"""The "ask about my work" chat: what goes into the prompt, and the endpoint."""

import asyncio
import json
import os
from datetime import date

import httpx
import pytest
from api.routes import ask as ask_route
from core import config
from db.dependency import get_db
from db.models.category import Category
from db.models.lab_notes import LabNote
from db.models.projects import Project
from db.session import Base
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from main import get_application
from services import ask
from services.rate_limit import ASK, RateLimiter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

PREFIX = "test-ask-"


# ── what goes into the prompt ────────────────────────────────────────────────


@pytest.fixture
def session_factory():
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db"
    )
    engine = create_engine(database_url)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    yield factory
    with factory() as db:
        for model in (Project, LabNote):
            db.query(model).filter(model.slug.startswith(PREFIX)).delete(
                synchronize_session=False
            )
        db.query(Category).filter(Category.name.startswith(PREFIX)).delete(
            synchronize_session=False
        )
        db.commit()


def add_project(db, name, published=True, **fields):
    category = db.query(Category).filter(Category.name == PREFIX + "cat").first()
    if category is None:
        category = Category(name=PREFIX + "cat", label="Test")
        db.add(category)
        db.flush()
    project = Project(
        category_id=category.id,
        slug=PREFIX + name,
        title=f"Project {name}",
        description=f"About {name}.",
        tags=["Tag"],
        year="2026",
        published=published,
        **fields,
    )
    db.add(project)
    db.commit()
    return project


def add_note(db, name, published=True):
    note = LabNote(
        slug=PREFIX + name,
        title=f"Note {name}",
        excerpt="x",
        content=f"Body of {name}.",
        tags=[],
        read_time="1 min",
        date=date(2026, 9, 30),
        published=published,
    )
    db.add(note)
    db.commit()
    return note


def test_only_published_content_reaches_the_prompt(session_factory):
    with session_factory() as db:
        add_project(db, "public", link="https://example.com/public")
        add_project(db, "draft", published=False)
        add_note(db, "public-note")
        add_note(db, "draft-note", published=False)

        snap = ask.build_snapshot(db, ask.content_key(db))

    assert "Project public" in snap.system_prompt
    assert "Body of public-note." in snap.system_prompt
    assert "Project draft" not in snap.system_prompt
    assert "Body of draft-note." not in snap.system_prompt
    titles = {s.title: s for s in snap.sources.values()}
    assert titles["Project public"].url == "https://example.com/public"
    assert titles["Note public-note"].url == f"/notes/{PREFIX}public-note"
    assert "Project draft" not in titles


def test_the_resume_is_in_the_prompt_without_private_details(session_factory):
    with session_factory() as db:
        snap = ask.build_snapshot(db, ask.content_key(db))

    resume = snap.sources["R1"]
    assert resume.kind == "resume" and resume.url == "/resume.pdf"
    assert "Rice University" in snap.system_prompt
    # The maintainer's comment at the top of the file stays out, and so does
    # the phone number from the LaTeX header.
    assert "<!--" not in snap.system_prompt
    assert "510" not in snap.system_prompt


def test_the_snapshot_is_rebuilt_only_when_content_changes(session_factory):
    ask._snapshot = None
    with session_factory() as db:
        project = add_project(db, "changing")
        first = ask.snapshot(db)
        assert ask.snapshot(db) is first

        project.published = False
        db.commit()
        second = ask.snapshot(db)

    assert second is not first
    assert "Project changing" in first.system_prompt
    assert "Project changing" not in second.system_prompt


def test_the_prompt_is_the_same_for_the_same_content(session_factory):
    # The prefix cache only helps if the prompt is byte-for-byte identical.
    with session_factory() as db:
        add_project(db, "a")
        add_project(db, "b")
        key = ask.content_key(db)
        assert (
            ask.build_snapshot(db, key).system_prompt
            == ask.build_snapshot(db, key).system_prompt
        )


def test_token_estimate_counts_chinese_per_character():
    assert ask.estimate_tokens("") == 0
    assert ask.estimate_tokens("a" * 35) == 10
    assert ask.estimate_tokens("研究") == 2
    assert ask.estimate_tokens("GNN 研究") == 4  # 4 / 3.5 + 2, rounded up


def test_prompt_size_and_budget_are_exported(session_factory, monkeypatch):
    from prometheus_client import REGISTRY

    monkeypatch.setattr(config, "ASK_CONTEXT_TOKENS", 16384)
    monkeypatch.setattr(config, "ASK_MAX_TOKENS", 400)
    with session_factory() as db:
        snap = ask.build_snapshot(db, ask.content_key(db))

    assert REGISTRY.get_sample_value("ask_prompt_tokens") == ask.estimate_tokens(
        snap.system_prompt
    )
    assert REGISTRY.get_sample_value("ask_prompt_budget_tokens") == (
        16384 - 400 - ask.QUESTION_TOKENS
    )
    assert REGISTRY.get_sample_value("ask_documents_dropped") == 0


def test_over_budget_leaves_out_the_oldest_notes_then_projects(
    session_factory, monkeypatch
):
    from prometheus_client import REGISTRY

    with session_factory() as db:
        add_project(db, "old-project")
        add_note(db, "old-note")
        add_note(db, "new-note")
        full = ask.build_snapshot(db, ask.content_key(db))

        def fit(tokens):
            # A context that leaves exactly `tokens` for the system prompt.
            monkeypatch.setattr(
                config,
                "ASK_CONTEXT_TOKENS",
                tokens + config.ASK_MAX_TOKENS + ask.QUESTION_TOKENS,
            )
            return ask.build_snapshot(db, ask.content_key(db))

        one_short = fit(ask.estimate_tokens(full.system_prompt) - 1)
        titles = {s.title for s in one_short.sources.values()}
        assert "Note old-note" not in titles
        assert {"Note new-note", "Project old-project", "Resume"} <= titles
        assert REGISTRY.get_sample_value("ask_documents_dropped") == 1

        resume_only = fit(1)
        assert set(resume_only.sources) == {"R1"}


# ── citations ────────────────────────────────────────────────────────────────

SOURCES = {
    "R1": ask.Source("R1", "resume", "Resume", "/resume.pdf"),
    "P1": ask.Source("P1", "project", "PAPIT", "https://github.com/x/papit"),
    "N1": ask.Source("N1", "note", "SVD", "/notes/svd"),
}


def test_citations_follow_first_mention_and_drop_made_up_ids():
    answer = "He built PAPIT [P1]. He studied at Rice [R1][P1]. See [P9] and [X1]."
    assert [s.id for s in ask.cited(answer, SOURCES)] == ["P1", "R1"]


# ── the endpoint ─────────────────────────────────────────────────────────────

SNAPSHOT = ask.Snapshot(key=(), system_prompt="RULES AND DOCUMENTS", sources=SOURCES)


def model_stream(pieces, usage=12):
    """A vLLM-style chat completions stream."""
    events = [
        {"choices": [{"delta": {"role": "assistant", "content": ""}}]},
        *({"choices": [{"delta": {"content": piece}}]} for piece in pieces),
        {"choices": [], "usage": {"completion_tokens": usage}},
    ]
    return "".join(f"data: {json.dumps(e)}\n\n" for e in events) + "data: [DONE]\n\n"


def events(body):
    """Parse a server-sent event stream into (event, data) pairs."""
    parsed = []
    for block in body.strip().split("\n\n"):
        lines = dict(line.split(": ", 1) for line in block.split("\n"))
        parsed.append((lines["event"], json.loads(lines["data"])))
    return parsed


@pytest.fixture
def model(monkeypatch):
    """Serve `reply` (a stream body, or a Response) as the model; returns what
    the backend sent it."""
    sent = {}

    def serve(reply):
        def handler(request):
            sent["json"] = json.loads(request.content)
            if isinstance(reply, httpx.Response):
                return reply
            return httpx.Response(
                200, text=reply, headers={"content-type": "text/event-stream"}
            )

        monkeypatch.setattr(ask, "_transport", httpx.MockTransport(handler))
        return sent

    monkeypatch.setattr(config, "ASK_URL", "http://model.test")
    monkeypatch.setattr(ask_route, "snapshot", lambda db: SNAPSHOT)
    monkeypatch.setattr(ask_route, "_generating", None)
    return serve


class FakeSession:
    closed = False

    def close(self):
        FakeSession.closed = True


@pytest.fixture
def app():
    FakeSession.closed = False
    application = get_application()
    application.dependency_overrides[get_db] = FakeSession
    return application


@pytest.fixture
def client(app):
    return TestClient(app)


def test_the_answer_streams_then_lists_what_it_cited(model, client):
    sent = model(model_stream(["He built ", "PAPIT [P1]", " and [P9]."]))

    response = client.post("/api/v1/ask", json={"question": "  What is PAPIT? "})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    got = events(response.text)
    assert got[:-1] == [
        ("token", {"text": "He built "}),
        ("token", {"text": "PAPIT [P1]"}),
        ("token", {"text": " and [P9]."}),
    ]
    assert got[-1] == (
        "done",
        {
            "citations": [
                {
                    "id": "P1",
                    "kind": "project",
                    "title": "PAPIT",
                    "url": "https://github.com/x/papit",
                }
            ]
        },
    )
    request = sent["json"]
    assert request["messages"] == [
        {"role": "system", "content": "RULES AND DOCUMENTS"},
        {"role": "user", "content": "What is PAPIT?"},
    ]
    assert request["stream"] is True
    assert request["chat_template_kwargs"] == {"enable_thinking": False}


def test_the_database_session_is_released_before_streaming(model, client):
    # Otherwise its pooled connection stays checked out for the whole answer.
    model(model_stream(["Hi."]))
    client.post("/api/v1/ask", json={"question": "Hi?"})
    assert FakeSession.closed


def test_a_model_error_mid_stream_ends_with_an_error_event(model, client):
    model(
        'data: {"choices": [{"delta": {"content": "He "}}]}\n\n'
        'data: {"error": {"message": "engine died"}}\n\ndata: [DONE]\n\n'
    )

    got = events(client.post("/api/v1/ask", json={"question": "Hi?"}).text)

    assert got[-1][0] == "error"
    assert "done" not in [name for name, _ in got]


def test_whitespace_around_a_question_does_not_count_toward_its_length(model, client):
    sent = model(model_stream(["Hi."]))
    question = "x" * ask.MAX_QUESTION_CHARS

    response = client.post("/api/v1/ask", json={"question": f"  {question} \n"})

    assert response.status_code == 200
    assert sent["json"]["messages"][-1]["content"] == question


def test_a_generation_slot_is_returned_after_each_answer(model, client, monkeypatch):
    monkeypatch.setattr(config, "ASK_MAX_CONCURRENT", 1)
    model(model_stream(["Hi."]))

    codes = [
        client.post("/api/v1/ask", json={"question": "Hi?"}).status_code
        for _ in range(3)
    ]

    assert codes == [200, 200, 200]


@pytest.mark.parametrize("question", ["", "   ", "x" * (ask.MAX_QUESTION_CHARS + 1)])
def test_empty_or_long_questions_are_rejected(model, client, question):
    model(model_stream(["unused"]))
    assert client.post("/api/v1/ask", json={"question": question}).status_code == 422


def test_no_model_configured_is_503(model, client, monkeypatch):
    monkeypatch.setattr(config, "ASK_URL", "")
    response = client.post("/api/v1/ask", json={"question": "Hi?"})
    assert response.status_code == 503
    assert response.headers["retry-after"] == "60"


def test_a_model_that_refuses_is_503_and_frees_its_slot(model, client, monkeypatch):
    monkeypatch.setattr(config, "ASK_MAX_CONCURRENT", 1)
    model(httpx.Response(500, text="boom"))

    first = client.post("/api/v1/ask", json={"question": "Hi?"})
    second = client.post("/api/v1/ask", json={"question": "Hi?"})

    assert first.status_code == second.status_code == 503
    assert "offline" in second.json()["detail"]


def test_all_slots_busy_is_503_without_calling_the_model(model, client, monkeypatch):
    sent = model(model_stream(["unused"]))
    monkeypatch.setattr(ask_route, "_generating", asyncio.Semaphore(0))

    response = client.post("/api/v1/ask", json={"question": "Hi?"})

    assert response.status_code == 503
    assert "Busy" in response.json()["detail"]
    assert sent == {}


def test_a_broken_stream_ends_with_an_error_event(model, client):
    model('data: {"choices": [{"delta": {"content": "He "}}]}\n\ndata: {not json\n\n')

    got = events(client.post("/api/v1/ask", json={"question": "Hi?"}).text)

    assert got[0] == ("token", {"text": "He "})
    assert got[-1][0] == "error"


# ── limits ───────────────────────────────────────────────────────────────────


@pytest.fixture
async def limited_client(app, redis):
    app.state.rate_limiter = RateLimiter(redis)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.mark.anyio
async def test_a_visitor_gets_ten_questions_an_hour(model, limited_client):
    model(model_stream(["Hi."]))

    async def ask_from(ip):
        response = await limited_client.post(
            "/api/v1/ask",
            json={"question": "Hi?"},
            headers={"CF-Connecting-IP": ip},
        )
        return response.status_code

    codes = [await ask_from("203.0.113.9") for _ in range(ASK.limit + 1)]

    assert codes == [200] * ASK.limit + [429]
    assert await ask_from("198.51.100.7") == 200


@pytest.mark.anyio
async def test_refused_questions_do_not_use_up_the_limits(
    model, limited_client, monkeypatch, redis
):
    model(model_stream(["Hi."]))
    headers = {"CF-Connecting-IP": "203.0.113.5"}

    monkeypatch.setattr(ask_route, "_generating", asyncio.Semaphore(0))
    busy = await limited_client.post(
        "/api/v1/ask", json={"question": "Hi?"}, headers=headers
    )
    monkeypatch.setattr(ask_route, "_generating", None)
    monkeypatch.setattr(config, "ASK_URL", "")
    off = await limited_client.post(
        "/api/v1/ask", json={"question": "Hi?"}, headers=headers
    )
    bad = await limited_client.post(
        "/api/v1/ask", json={"question": ""}, headers=headers
    )

    assert (busy.status_code, off.status_code, bad.status_code) == (503, 503, 422)
    assert await redis.exists(RateLimiter.key(ASK, "203.0.113.5")) == 0
    assert await redis.exists(RateLimiter.key(ask_route.ASK_ALL, "all")) == 0


@pytest.mark.anyio
async def test_every_visitor_counts_against_the_daily_site_budget(
    model, limited_client, redis
):
    model(model_stream(["Hi."]))

    for ip in ("203.0.113.1", "203.0.113.2"):
        await limited_client.post(
            "/api/v1/ask", json={"question": "Hi?"}, headers={"CF-Connecting-IP": ip}
        )

    bucket = await redis.hgetall(RateLimiter.key(ask_route.ASK_ALL, "all"))
    assert float(bucket[b"tokens"]) == pytest.approx(ask_route.ASK_ALL.limit - 2, 0.01)


def test_every_ask_counter_series_exists_from_the_start():
    from prometheus_client import REGISTRY

    for result in ("answered", "busy", "unavailable", "error", "cancelled"):
        assert (
            REGISTRY.get_sample_value("ask_requests_total", {"result": result})
            is not None
        )

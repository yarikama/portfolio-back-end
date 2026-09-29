import asyncio
import json
import math
import os

import httpx
import pytest
from api.dependencies import get_current_admin
from core import config
from db.dependency import get_db
from db.models.autocomplete import AutocompleteSuggestion
from db.session import Base
from fastapi.testclient import TestClient
from main import get_application
from services import autocomplete
from services.autocomplete import Completion, build_prompt, shape_suggestion
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

VERSION = "test-model@autocomplete-tests"


def lp(prob):
    return math.log(prob)


# ── build_prompt ─────────────────────────────────────────────────────────────


def test_prompt_puts_the_title_as_a_heading():
    assert build_prompt("Some text", "My Note").text == "# My Note\n\nSome text"
    assert build_prompt("Some text", "  ").text == "Some text"


def test_prompt_drops_trailing_spaces_but_remembers_them():
    prompt = build_prompt("The model was ", "")
    assert prompt.text == "The model was"
    assert prompt.trailing_space == " "


def test_prompt_keeps_a_trailing_newline():
    prompt = build_prompt("A paragraph.\n", "")
    assert prompt.text == "A paragraph.\n"
    assert prompt.trailing_space == ""


def test_prompt_keeps_only_the_tail_of_long_notes():
    prompt = build_prompt("x" * 5000 + "end", "")
    assert len(prompt.text) == autocomplete.MAX_CONTEXT_CHARS
    assert prompt.text.endswith("end")


# ── shape_suggestion ─────────────────────────────────────────────────────────


def test_suggestion_stops_at_the_first_unsure_token():
    tokens = [(" the", lp(0.9)), (" model", lp(0.6)), (" learns", lp(0.2))]
    assert shape_suggestion(tokens, "", 0.5) == " the model"


def test_suggestion_stops_after_a_sentence_end():
    tokens = [(" it", lp(0.9)), (" works.", lp(0.9)), (" Then", lp(0.9))]
    assert shape_suggestion(tokens, "", 0.5) == " it works."


def test_suggestion_is_empty_when_the_first_token_is_unsure():
    assert shape_suggestion([(" maybe", lp(0.3))], "", 0.5) == ""


def test_suggestion_drops_the_space_the_author_already_typed():
    tokens = [(" was", lp(0.9)), (" his", lp(0.8))]
    assert shape_suggestion(tokens, " ", 0.5) == "was his"


def test_suggestion_continuing_the_word_does_not_fit_after_a_space():
    # The author typed "portfol" + space; "io" would glue onto the old word.
    assert shape_suggestion([("io", lp(0.9))], " ", 0.5) == ""


def test_suggestion_can_finish_the_current_word():
    assert shape_suggestion([("lete", lp(0.9))], "", 0.5) == "lete"


# ── endpoints ────────────────────────────────────────────────────────────────


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
        db.query(AutocompleteSuggestion).filter(
            AutocompleteSuggestion.model_version == VERSION
        ).delete(synchronize_session=False)
        db.commit()


@pytest.fixture
def client(session_factory, monkeypatch):
    monkeypatch.setattr(config, "AUTOCOMPLETE_URL", "http://model.test")
    monkeypatch.setattr(config, "AUTOCOMPLETE_MODEL_VERSION", VERSION)
    monkeypatch.setattr(config, "AUTOCOMPLETE_MIN_TOKEN_PROB", 0.5)

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app = get_application()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_admin] = lambda: "admin"
    return TestClient(app)


def fake_model(monkeypatch, tokens=None, error=None):
    async def complete(prompt, min_prob):
        if error:
            raise error
        return Completion(
            text="".join(t for t, _ in tokens), tokens=tokens, latency_ms=42
        )

    monkeypatch.setattr(autocomplete, "complete", complete)


def test_a_confident_completion_is_shown_and_recorded(
    client, session_factory, monkeypatch
):
    fake_model(monkeypatch, [(" was", lp(0.9)), (" his", lp(0.7)), (" 3D", lp(0.1))])

    response = client.post(
        "/api/v1/admin/complete",
        json={"prefix": "What impressed me ", "title": "Notes"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["suggestion"] == "was his"
    with session_factory() as db:
        row = db.get(AutocompleteSuggestion, data["id"])
        assert row.prompt == "# Notes\n\nWhat impressed me"
        assert row.completion == " was his 3D"
        assert row.suggestion == "was his"
        assert row.model_version == VERSION
        assert row.latency_ms == 42
        assert row.min_token_prob == 0.5
        assert row.outcome is None


def test_an_unsure_completion_shows_nothing_and_is_not_recorded(
    client, session_factory, monkeypatch
):
    fake_model(monkeypatch, [(" perhaps", lp(0.2))])

    response = client.post("/api/v1/admin/complete", json={"prefix": "Hello"})

    assert response.json()["data"] == {"id": None, "suggestion": ""}
    with session_factory() as db:
        assert (
            db.query(AutocompleteSuggestion)
            .filter(AutocompleteSuggestion.model_version == VERSION)
            .count()
            == 0
        )


def test_a_model_failure_shows_nothing(client, monkeypatch):
    fake_model(monkeypatch, error=httpx.ConnectError("model down"))

    response = client.post("/api/v1/admin/complete", json={"prefix": "Hello"})

    assert response.status_code == 200
    assert response.json()["data"] == {"id": None, "suggestion": ""}


def test_unconfigured_autocomplete_answers_503(client, monkeypatch):
    monkeypatch.setattr(config, "AUTOCOMPLETE_URL", "")
    assert (
        client.post("/api/v1/admin/complete", json={"prefix": "Hi"}).status_code == 503
    )


def test_feedback_is_recorded_once(client, session_factory, monkeypatch):
    fake_model(monkeypatch, [(" world", lp(0.9))])
    suggestion_id = client.post(
        "/api/v1/admin/complete", json={"prefix": "Hello"}
    ).json()["data"]["id"]

    first = client.post(
        f"/api/v1/admin/complete/{suggestion_id}/feedback",
        json={"outcome": "accepted", "acceptedChars": 6},
    )
    second = client.post(
        f"/api/v1/admin/complete/{suggestion_id}/feedback",
        json={"outcome": "rejected"},
    )

    assert first.status_code == second.status_code == 204
    with session_factory() as db:
        row = db.get(AutocompleteSuggestion, suggestion_id)
        assert row.outcome == "accepted"
        assert row.accepted_chars == 6
        assert row.resolved_at is not None


def test_feedback_for_an_unknown_suggestion_is_404(client):
    response = client.post(
        "/api/v1/admin/complete/00000000-0000-0000-0000-000000000000/feedback",
        json={"outcome": "rejected"},
    )
    assert response.status_code == 404


def test_autocomplete_needs_the_admin_token():
    client = TestClient(get_application())
    assert client.post("/api/v1/admin/complete", json={"prefix": "Hi"}).status_code in (
        401,
        403,
    )


# ── streaming from the model ─────────────────────────────────────────────────


def sse(tokens, done=True):
    """A vLLM-style completions stream: one token and its logprob per event."""
    events = [
        "data: "
        + json.dumps(
            {
                "choices": [
                    {
                        "text": token,
                        "logprobs": {"tokens": [token], "token_logprobs": [logprob]},
                    }
                ]
            }
        )
        for token, logprob in tokens
    ]
    if done:
        events.append("data: [DONE]")
    return "\n\n".join(events) + "\n\n"


@pytest.fixture
def model_stream(monkeypatch):
    sent = {}

    def serve(body):
        def handler(request):
            sent["json"] = json.loads(request.content)
            return httpx.Response(
                200, text=body, headers={"content-type": "text/event-stream"}
            )

        monkeypatch.setattr(autocomplete, "_transport", httpx.MockTransport(handler))
        return sent

    monkeypatch.setattr(config, "AUTOCOMPLETE_URL", "http://model.test")
    return serve


def test_streaming_stops_at_the_first_unsure_token(model_stream):
    sent = model_stream(
        sse([(" the", lp(0.9)), (" model", lp(0.2)), (" learns", lp(0.9))])
    )

    result = asyncio.run(autocomplete.complete("prompt", 0.5))

    assert sent["json"]["stream"] is True
    assert sent["json"]["logprobs"] == 0
    # Read up to and including the unsure token, then stopped.
    assert [t for t, _ in result.tokens] == [" the", " model"]
    assert result.text == " the model"
    assert shape_suggestion(result.tokens, "", 0.5) == " the"


def test_streaming_stops_after_a_sentence_end(model_stream):
    model_stream(sse([(" works.", lp(0.9)), (" Then", lp(0.9))]))

    result = asyncio.run(autocomplete.complete("prompt", 0.5))

    assert [t for t, _ in result.tokens] == [" works."]


def test_streaming_reads_to_the_end_when_every_token_is_sure(model_stream):
    model_stream(sse([(" a", lp(0.9)), (" b", lp(0.8))]))

    result = asyncio.run(autocomplete.complete("prompt", 0.5))

    assert result.text == " a b"


def test_streaming_surfaces_http_errors(monkeypatch):
    monkeypatch.setattr(config, "AUTOCOMPLETE_URL", "http://model.test")
    monkeypatch.setattr(
        autocomplete,
        "_transport",
        httpx.MockTransport(lambda request: httpx.Response(503)),
    )
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(autocomplete.complete("prompt", 0.5))

import pytest
import services.predict as predict
from core import events
from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import get_application


def test_preload_model(monkeypatch):
    called = {}

    def fake_get_model(cls, loader):
        called["called"] = True

    monkeypatch.setattr(
        predict.MachineLearningModelHandlerScore,
        "get_model",
        classmethod(fake_get_model),
    )
    events.preload_model()
    assert called.get("called") is True


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
@pytest.mark.parametrize("memoize", [True, False])
async def test_lifespan_preloads_model_only_when_memoizing(monkeypatch, memoize):
    called = {}

    def fake_preload():
        called["called"] = True

    monkeypatch.setattr(events, "preload_model", fake_preload)
    monkeypatch.setattr(events, "MEMOIZATION_FLAG", memoize)

    async with events.lifespan(FastAPI()):
        pass
    assert called.get("called", False) is memoize


def test_get_application():
    app = get_application()
    assert isinstance(app, FastAPI)


def test_health_returns_ok():
    client = TestClient(get_application())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

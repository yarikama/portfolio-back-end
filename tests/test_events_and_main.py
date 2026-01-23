import services.predict as predict
from core import events
from fastapi import FastAPI
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


def test_create_start_app_handler(monkeypatch):
    called = {}

    def fake_preload():
        called["called"] = True

    monkeypatch.setattr(events, "preload_model", fake_preload)
    monkeypatch.setattr(events, "MEMOIZATION_FLAG", True)

    app = FastAPI()
    handler = events.create_start_app_handler(app)
    handler()
    assert called.get("called") is True


def test_get_application():
    app = get_application()
    assert isinstance(app, FastAPI)

import json
from pathlib import Path

from api.routes import predictor
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def sample_input():
    example_path = (
        Path(__file__).resolve().parents[1]
        / "ml"
        / "model"
        / "examples"
        / "example.json"
    )
    return json.loads(example_path.read_text())


def test_predict_endpoint(monkeypatch):
    monkeypatch.setattr(predictor, "get_prediction", lambda data_point: [1.0])
    response = client.post("/api/v1/predict", json=sample_input())
    assert response.status_code == 200
    assert response.json() == {"prediction": 1.0, "prediction_label": "label ok"}


def test_health_endpoint(monkeypatch):
    monkeypatch.setattr(predictor, "get_prediction", lambda data_point: [1.0])
    monkeypatch.setattr(
        predictor,
        "INPUT_EXAMPLE",
        str(
            Path(__file__).resolve().parents[1]
            / "ml"
            / "model"
            / "examples"
            / "example.json"
        ),
    )
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": True}

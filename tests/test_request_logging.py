import json
import os

import pytest
from api.routes import predictor
from db.models.log import RequestLog
from db.session import Base
from schemas.prediction import MachineLearningDataInput
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_predict_logs_request_response(monkeypatch):
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_db"
    )
    engine = create_engine(database_url)
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    monkeypatch.setattr(predictor, "SessionLocal", testing_session_local)
    monkeypatch.setattr(predictor, "get_prediction", lambda data: [1])

    payload = {
        "feature1": 1.0,
        "feature2": 2.0,
        "feature3": 3.0,
        "feature4": 4.0,
        "feature5": 5.0,
    }
    data = MachineLearningDataInput(**payload)

    response = await predictor.predict(data)
    assert response.prediction == 1.0

    db = testing_session_local()
    logs = db.query(RequestLog).all()
    assert len(logs) == 1
    log = logs[0]
    assert json.loads(log.request) == data.model_dump()
    assert json.loads(log.response) == response.model_dump()
    db.close()

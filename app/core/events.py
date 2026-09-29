from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import joblib
from core.config import MEMOIZATION_FLAG
from fastapi import FastAPI


def preload_model():
    """
    In order to load model on memory to each worker
    """
    from services.predict import MachineLearningModelHandlerScore

    MachineLearningModelHandlerScore.get_model(joblib.load)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if MEMOIZATION_FLAG:
        preload_model()
    yield

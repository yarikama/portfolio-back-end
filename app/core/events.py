from typing import Callable

import joblib
from core.config import MEMOIZATION_FLAG
from fastapi import FastAPI


def preload_model():
    """
    In order to load model on memory to each worker
    """
    from services.predict import MachineLearningModelHandlerScore

    MachineLearningModelHandlerScore.get_model(joblib.load)


def create_start_app_handler(app: FastAPI) -> Callable:
    def start_app() -> None:
        if MEMOIZATION_FLAG:
            preload_model()

    return start_app

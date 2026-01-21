from fastapi import APIRouter

from api.routes import predictor
from api.routes import projects

router = APIRouter()
router.include_router(predictor.router, tags=["predictor"], prefix="/v1")
router.include_router(projects.router, tags=["projects"], prefix="/v1")

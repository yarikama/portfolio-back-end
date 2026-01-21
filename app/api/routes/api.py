from api.routes import predictor, projects
from fastapi import APIRouter

router = APIRouter()
router.include_router(predictor.router, tags=["predictor"], prefix="/v1")
router.include_router(projects.router, tags=["projects"], prefix="/v1")

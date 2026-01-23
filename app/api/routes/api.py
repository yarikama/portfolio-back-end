from api.routes import auth, categories, contact, lab_notes, predictor, projects
from fastapi import APIRouter

router = APIRouter()
router.include_router(auth.router, tags=["auth"], prefix="/v1")
router.include_router(predictor.router, tags=["predictor"], prefix="/v1")
router.include_router(categories.router, tags=["categories"], prefix="/v1")
router.include_router(projects.router, tags=["projects"], prefix="/v1")
router.include_router(lab_notes.router, tags=["lab-notes"], prefix="/v1")
router.include_router(contact.router, tags=["contact"], prefix="/v1")

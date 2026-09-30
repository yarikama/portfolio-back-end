from api.routes import (
    ask,
    auth,
    autocomplete,
    categories,
    contact,
    lab_notes,
    projects,
    upload,
)
from fastapi import APIRouter

router = APIRouter()
router.include_router(auth.router, tags=["auth"], prefix="/v1")
router.include_router(categories.router, tags=["categories"], prefix="/v1")
router.include_router(projects.router, tags=["projects"], prefix="/v1")
router.include_router(lab_notes.router, tags=["lab-notes"], prefix="/v1")
router.include_router(contact.router, tags=["contact"], prefix="/v1")
router.include_router(upload.router, tags=["upload"], prefix="/v1")
router.include_router(autocomplete.router, tags=["autocomplete"], prefix="/v1")
router.include_router(ask.router, tags=["ask"], prefix="/v1")

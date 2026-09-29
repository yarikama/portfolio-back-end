from api.routes.api import router as api_router
from api.routes.health import router as health_router
from core.config import API_PREFIX, DEBUG, PROJECT_NAME, VERSION
from core.events import lifespan
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def get_application() -> FastAPI:
    application = FastAPI(
        title=PROJECT_NAME, debug=DEBUG, version=VERSION, lifespan=lifespan
    )

    # CORS settings
    origins = [
        "http://localhost:3000",  # Local frontend dev
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://yarikama.com",  # Production frontend
        "https://www.yarikama.com",
    ]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
    application.include_router(api_router, prefix=API_PREFIX)
    return application


app = get_application()

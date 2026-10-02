from api.cache import PublicCacheMiddleware
from api.middleware import PublicRateLimitMiddleware
from api.routes.api import router as api_router
from api.routes.health import router as health_router
from api.security import SecurityHeadersMiddleware
from core.config import API_PREFIX, DEBUG, PROJECT_NAME, VERSION
from core.events import lifespan
from core.tracing import setup_tracing
from db.session import engine
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

    # Before CORS, so that CORS wraps it and its 429s carry CORS headers.
    application.add_middleware(PublicRateLimitMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        # Admin requests carry an Authorization header, so the browser asks
        # permission (a preflight OPTIONS round trip) before them. Starlette's
        # default lets it remember the answer for 10 minutes; 2 hours is
        # Chrome's cap, and saves a round trip on the first autocomplete
        # request after every pause in writing.
        max_age=7200,
        # Lets the site read how long to wait after a 429.
        expose_headers=["Retry-After"],
    )
    # Outermost: rewrites what CORS added on responses Cloudflare may cache.
    application.add_middleware(PublicCacheMiddleware)
    # On every response, including 429s and cached copies.
    application.add_middleware(SecurityHeadersMiddleware)

    application.include_router(health_router)
    application.include_router(api_router, prefix=API_PREFIX)
    return application


app = get_application()
setup_tracing(app, engine)

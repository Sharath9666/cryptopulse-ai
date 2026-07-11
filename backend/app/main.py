"""
CryptoPulse AI Backend Application Entrypoint.
Initializes the FastAPI application, registers middleware, exception handlers, and routes.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config.settings import settings
from app.core.lifespan import lifespan
from app.exceptions.handlers import register_exception_handlers
from app.middleware.logging import RequestLoggingMiddleware


def create_app() -> FastAPI:
    """
    Application factory to create and configure the FastAPI app instance.
    """
    fastapi_app = FastAPI(
        title=settings.APP_NAME,
        description="Production-grade backend for CryptoPulse AI platform.",
        version="0.1.0",
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    # 1. CORS Middleware setup
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_HOSTS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Custom Request Logging Middleware
    fastapi_app.add_middleware(RequestLoggingMiddleware)

    # 3. Global Exception Handlers
    register_exception_handlers(fastapi_app)

    # 4. Mount API Routes
    fastapi_app.include_router(api_router)

    return fastapi_app


app = create_app()

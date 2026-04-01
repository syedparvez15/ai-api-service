"""
Application factory.

Creates and configures the FastAPI instance.
Keeping this separate from main.py makes testing easier —
tests can import create_app() without starting the server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.middleware.exception_handlers import register_exception_handlers
from src.middleware.request_logger import RequestLoggingMiddleware
from src.routes import ai_routes, health_routes
from src.utils.logger import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A production-grade backend service that exposes AI capabilities "
            "via a clean REST API. Supports text summarization, prompt-based generation, "
            "text classification, and multi-turn chat."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # --- Middleware (order matters: outermost = last registered) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Routers ---
    app.include_router(health_routes.router)
    app.include_router(ai_routes.router)

    return app

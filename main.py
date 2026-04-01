"""
Application entrypoint.

Run with:
    uvicorn main:app --reload                     # development
    uvicorn main:app --host 0.0.0.0 --port 8000   # production
"""

import uvicorn
from src.app import create_app
from src.config import get_settings

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
        log_config=None,  # We manage logging via structlog
    )

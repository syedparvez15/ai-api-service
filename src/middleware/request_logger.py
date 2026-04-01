"""
Request / response logging middleware.

Logs every request with method, path, status code, and duration.
Attaches a request ID for distributed tracing.
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.utils.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        start = time.perf_counter()

        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            request_id=request_id,
            client=request.client.host if request.client else "unknown",
        )

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "http.response",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(elapsed_ms, 2),
            request_id=request_id,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms:.2f}ms"
        return response

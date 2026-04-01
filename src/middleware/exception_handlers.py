"""
Global exception handlers.

All unhandled errors funnel through here and are converted
into a consistent ErrorResponse envelope before reaching the client.
"""

import traceback
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.models.schemas import ErrorDetail, ErrorResponse
from src.utils.exceptions import AIServiceException, ErrorCode
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _extract_request_id(request: Request) -> str | None:
    return request.headers.get("X-Request-ID")


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AIServiceException)
    async def ai_service_exception_handler(
        request: Request, exc: AIServiceException
    ) -> JSONResponse:
        logger.warning(
            "exception.ai_service",
            error_code=exc.error_code,
            message=exc.message,
            path=request.url.path,
        )
        body = ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details or None,
            request_id=_extract_request_id(request),
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(exclude_none=True),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            ErrorDetail(
                field=" → ".join(str(loc) for loc in err["loc"][1:]) or "body",
                message=err["msg"],
            )
            for err in exc.errors()
        ]
        logger.info(
            "exception.validation",
            path=request.url.path,
            error_count=len(details),
        )
        body = ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Request validation failed.",
            details=[d.model_dump(exclude_none=True) for d in details],
            request_id=_extract_request_id(request),
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=body.model_dump(exclude_none=True),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(
            "exception.unhandled",
            path=request.url.path,
            error=str(exc),
            traceback=traceback.format_exc(),
        )
        body = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="An unexpected error occurred. Please try again later.",
            request_id=_extract_request_id(request),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=body.model_dump(exclude_none=True),
        )

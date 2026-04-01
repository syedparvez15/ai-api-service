"""
Domain-specific exceptions for the AI API Service.
All exceptions map to structured HTTP error responses.
"""

from enum import Enum


class ErrorCode(str, Enum):
    # Validation
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_INPUT = "INVALID_INPUT"
    TEXT_TOO_LONG = "TEXT_TOO_LONG"
    TEXT_TOO_SHORT = "TEXT_TOO_SHORT"

    # AI Service
    AI_SERVICE_ERROR = "AI_SERVICE_ERROR"
    AI_TIMEOUT = "AI_TIMEOUT"
    AI_QUOTA_EXCEEDED = "AI_QUOTA_EXCEEDED"
    AI_CONTENT_FILTERED = "AI_CONTENT_FILTERED"

    # Auth
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # General
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_FOUND = "NOT_FOUND"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class AIServiceException(Exception):
    """Base exception for all AI service errors."""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ValidationException(AIServiceException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            message=message,
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=422,
            details=details,
        )


class TextTooLongException(AIServiceException):
    def __init__(self, max_chars: int, received: int):
        super().__init__(
            message=f"Input text exceeds maximum allowed length of {max_chars} characters.",
            error_code=ErrorCode.TEXT_TOO_LONG,
            status_code=422,
            details={"max_chars": max_chars, "received": received},
        )


class AIProviderException(AIServiceException):
    def __init__(self, message: str, provider: str = "openai"):
        super().__init__(
            message=message,
            error_code=ErrorCode.AI_SERVICE_ERROR,
            status_code=502,
            details={"provider": provider},
        )


class AIQuotaExceededException(AIServiceException):
    def __init__(self):
        super().__init__(
            message="AI provider quota has been exceeded. Please try again later.",
            error_code=ErrorCode.AI_QUOTA_EXCEEDED,
            status_code=503,
        )


class AITimeoutException(AIServiceException):
    def __init__(self, timeout_seconds: float):
        super().__init__(
            message=f"AI provider did not respond within {timeout_seconds}s.",
            error_code=ErrorCode.AI_TIMEOUT,
            status_code=504,
            details={"timeout_seconds": timeout_seconds},
        )


class UnauthorizedException(AIServiceException):
    def __init__(self):
        super().__init__(
            message="Missing or invalid API key.",
            error_code=ErrorCode.UNAUTHORIZED,
            status_code=401,
        )


class RateLimitException(AIServiceException):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please slow down your requests.",
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details={"retry_after_seconds": retry_after},
        )

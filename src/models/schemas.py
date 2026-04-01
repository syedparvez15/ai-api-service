"""
Pydantic v2 models for request validation and response serialization.
Strict types ensure no data leaks into the AI layer.
"""

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class BaseRequest(BaseModel):
    """Common fields every request may carry."""
    request_id: str | None = Field(
        default=None,
        description="Optional caller-supplied idempotency / tracing ID.",
        examples=["req_abc123"],
    )


class BaseResponse(BaseModel):
    """Envelope every success response is wrapped in."""
    success: bool = True
    request_id: str | None = None
    processing_time_ms: float | None = None


# ---------------------------------------------------------------------------
# Summarization
# ---------------------------------------------------------------------------

class SummarizeRequest(BaseRequest):
    text: str = Field(
        ...,
        min_length=50,
        max_length=10_000,
        description="The body of text to summarize.",
        examples=["Large article or document content goes here..."],
    )
    max_sentences: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Target number of sentences in the summary.",
    )
    style: str = Field(
        default="concise",
        description="Summary style: concise | detailed | bullet_points",
        examples=["concise"],
    )

    @field_validator("style")
    @classmethod
    def validate_style(cls, v: str) -> str:
        allowed = {"concise", "detailed", "bullet_points"}
        if v not in allowed:
            raise ValueError(f"style must be one of {allowed}")
        return v


class SummarizeResponse(BaseResponse):
    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float
    model_used: str


# ---------------------------------------------------------------------------
# Prompt-based generation
# ---------------------------------------------------------------------------

class GenerateRequest(BaseRequest):
    prompt: str = Field(
        ...,
        min_length=5,
        max_length=4_000,
        description="The instruction or question to send to the model.",
        examples=["Explain the concept of microservices in simple terms."],
    )
    max_tokens: int = Field(default=512, ge=50, le=2048)
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature — higher = more creative.",
    )
    system_prompt: str | None = Field(
        default=None,
        max_length=1_000,
        description="Optional system-level instruction for the model.",
    )


class GenerateResponse(BaseResponse):
    generated_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model_used: str
    finish_reason: str


# ---------------------------------------------------------------------------
# Text classification
# ---------------------------------------------------------------------------

class ClassificationCategory(str, Enum):
    TECHNICAL = "technical"
    BUSINESS = "business"
    CREATIVE = "creative"
    LEGAL = "legal"
    MEDICAL = "medical"
    GENERAL = "general"
    UNKNOWN = "unknown"


class ClassifyRequest(BaseRequest):
    text: str = Field(
        ...,
        min_length=10,
        max_length=5_000,
        description="Text to classify.",
    )
    categories: list[str] | None = Field(
        default=None,
        description="Optional custom category list. Defaults to built-in taxonomy.",
        max_length=10,
    )

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            if len(v) < 2:
                raise ValueError("Provide at least 2 categories.")
            v = [c.strip().lower() for c in v]
        return v


class CategoryScore(BaseModel):
    category: str
    confidence: float = Field(ge=0.0, le=1.0)


class ClassifyResponse(BaseResponse):
    primary_category: str
    confidence: float
    all_scores: list[CategoryScore]
    reasoning: str
    model_used: str


# ---------------------------------------------------------------------------
# Chat (bonus feature)
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=4_000)


class ChatRequest(BaseRequest):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=20)
    max_tokens: int = Field(default=512, ge=50, le=2048)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: str | None = Field(default=None, max_length=1_000)

    @model_validator(mode="after")
    def validate_last_message_is_user(self) -> "ChatRequest":
        if self.messages and self.messages[-1].role != "user":
            raise ValueError("The last message in the conversation must have role='user'.")
        return self


class ChatResponse(BaseResponse):
    reply: str
    role: str = "assistant"
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model_used: str
    finish_reason: str


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: list[ErrorDetail] | dict[str, Any] | None = None
    request_id: str | None = None

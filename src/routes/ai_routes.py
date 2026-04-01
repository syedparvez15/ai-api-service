"""
AI API routes.

All routes follow the pattern:
  Route handler → Controller → Service → AI Provider → Response
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from src.controllers.ai_controller import (
    SummarizationController,
    GenerationController,
    ClassificationController,
    ChatController,
)
from src.dependencies import (
    get_summarization_service,
    get_generation_service,
    get_classification_service,
    get_chat_service,
)
from src.models.schemas import (
    SummarizeRequest,
    SummarizeResponse,
    GenerateRequest,
    GenerateResponse,
    ClassifyRequest,
    ClassifyResponse,
    ChatRequest,
    ChatResponse,
)

router = APIRouter(prefix="/api/v1", tags=["AI"])


# ---------------------------------------------------------------------------
# POST /summarize
# ---------------------------------------------------------------------------

@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize text",
    description=(
        "Condenses a body of text into a shorter summary. "
        "Supports concise, detailed, and bullet-point styles."
    ),
    responses={
        200: {"description": "Summary generated successfully."},
        422: {"description": "Validation error — check request body."},
        502: {"description": "AI provider error."},
    },
)
async def summarize(
    request: SummarizeRequest,
    summarization_service=Depends(get_summarization_service),
) -> SummarizeResponse:
    controller = SummarizationController(summarization_service)
    return await controller.handle(request)


# ---------------------------------------------------------------------------
# POST /generate
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate text from a prompt",
    description=(
        "Sends a prompt to the AI model and returns the generated completion. "
        "Optionally accepts a custom system prompt."
    ),
)
async def generate(
    request: GenerateRequest,
    generation_service=Depends(get_generation_service),
) -> GenerateResponse:
    controller = GenerationController(generation_service)
    return await controller.handle(request)


# ---------------------------------------------------------------------------
# POST /classify
# ---------------------------------------------------------------------------

@router.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Classify text into categories",
    description=(
        "Classifies the input text into one or more categories with confidence scores. "
        "Uses a built-in taxonomy by default; custom categories are supported."
    ),
)
async def classify(
    request: ClassifyRequest,
    classification_service=Depends(get_classification_service),
) -> ClassifyResponse:
    controller = ClassificationController(classification_service)
    return await controller.handle(request)


# ---------------------------------------------------------------------------
# POST /chat (bonus)
# ---------------------------------------------------------------------------

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Multi-turn chat",
    description=(
        "Accepts a conversation history and returns the next assistant reply. "
        "The client is responsible for maintaining and replaying message history."
    ),
)
async def chat(
    request: ChatRequest,
    chat_service=Depends(get_chat_service),
) -> ChatResponse:
    controller = ChatController(chat_service)
    return await controller.handle(request)

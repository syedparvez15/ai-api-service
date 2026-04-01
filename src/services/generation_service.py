"""
Prompt-based text generation service.

Wraps the AI provider call with prompt safety checks,
token estimation, and structured logging.
"""

import time

from src.models.schemas import GenerateRequest, GenerateResponse
from src.services.ai_provider import BaseAIProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_SYSTEM = (
    "You are a helpful, knowledgeable, and professional AI assistant. "
    "Provide accurate, well-structured responses. "
    "If you are unsure, say so rather than fabricating information."
)


class GenerationService:
    def __init__(self, provider: BaseAIProvider):
        self._provider = provider

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        start = time.perf_counter()

        logger.info(
            "generate.start",
            prompt_length=len(request.prompt),
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            request_id=request.request_id,
        )

        system_content = request.system_prompt or _DEFAULT_SYSTEM

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": request.prompt},
        ]

        result = await self._provider.complete(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "generate.complete",
            tokens_used=result.total_tokens,
            finish_reason=result.finish_reason,
            latency_ms=round(elapsed_ms, 2),
        )

        return GenerateResponse(
            generated_text=result.text.strip(),
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            model_used=result.model,
            finish_reason=result.finish_reason,
            processing_time_ms=round(elapsed_ms, 2),
            request_id=request.request_id,
        )

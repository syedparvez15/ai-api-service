"""
Multi-turn chat service (bonus feature).

Handles stateless multi-turn conversation payloads.
The caller is responsible for maintaining message history.
"""

import time

from src.models.schemas import ChatRequest, ChatResponse
from src.services.ai_provider import BaseAIProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_SYSTEM = (
    "You are a helpful, thoughtful, and concise AI assistant. "
    "Maintain context across the conversation. "
    "Be direct, accurate, and professional."
)


class ChatService:
    def __init__(self, provider: BaseAIProvider):
        self._provider = provider

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.perf_counter()

        logger.info(
            "chat.start",
            message_count=len(request.messages),
            max_tokens=request.max_tokens,
            request_id=request.request_id,
        )

        # Build message list with optional system override
        system_content = request.system_prompt or _DEFAULT_SYSTEM
        messages = [{"role": "system", "content": system_content}]
        messages += [{"role": m.role, "content": m.content} for m in request.messages]

        result = await self._provider.complete(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "chat.complete",
            tokens_used=result.total_tokens,
            latency_ms=round(elapsed_ms, 2),
        )

        return ChatResponse(
            reply=result.text.strip(),
            role="assistant",
            prompt_tokens=result.prompt_tokens,
            completion_tokens=result.completion_tokens,
            total_tokens=result.total_tokens,
            model_used=result.model,
            finish_reason=result.finish_reason,
            processing_time_ms=round(elapsed_ms, 2),
            request_id=request.request_id,
        )

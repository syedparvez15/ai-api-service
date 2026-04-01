"""
Summarization service.

Builds structured prompts and delegates to the AI provider.
Handles post-processing and response normalization.
"""

import time

from src.models.schemas import SummarizeRequest, SummarizeResponse
from src.services.ai_provider import BaseAIProvider
from src.utils.exceptions import TextTooLongException
from src.utils.logger import get_logger

logger = get_logger(__name__)

MAX_CHARS = 10_000

_STYLE_INSTRUCTIONS = {
    "concise": "Write a concise summary in {n} sentences. Be direct and factual.",
    "detailed": (
        "Write a detailed summary in {n} sentences. "
        "Preserve nuance and key supporting details."
    ),
    "bullet_points": (
        "Write a summary as {n} bullet points. "
        "Each bullet should capture one distinct idea. "
        "Start every bullet with '•'."
    ),
}


class SummarizationService:
    def __init__(self, provider: BaseAIProvider):
        self._provider = provider

    async def summarize(self, request: SummarizeRequest) -> SummarizeResponse:
        if len(request.text) > MAX_CHARS:
            raise TextTooLongException(max_chars=MAX_CHARS, received=len(request.text))

        start = time.perf_counter()
        logger.info(
            "summarize.start",
            text_length=len(request.text),
            style=request.style,
            max_sentences=request.max_sentences,
            request_id=request.request_id,
        )

        style_instruction = _STYLE_INSTRUCTIONS[request.style].format(
            n=request.max_sentences
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a professional summarization assistant. "
                    "Your summaries are accurate, neutral, and well-structured. "
                    "Never add information that is not present in the source text."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"{style_instruction}\n\n"
                    f"TEXT TO SUMMARIZE:\n{request.text}"
                ),
            },
        ]

        result = await self._provider.complete(
            messages=messages,
            max_tokens=512,
            temperature=0.3,  # Low temp for factual accuracy
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        summary = result.text.strip()
        compression_ratio = round(len(summary) / max(len(request.text), 1), 4)

        logger.info(
            "summarize.complete",
            summary_length=len(summary),
            compression_ratio=compression_ratio,
            tokens_used=result.total_tokens,
            latency_ms=round(elapsed_ms, 2),
        )

        return SummarizeResponse(
            summary=summary,
            original_length=len(request.text),
            summary_length=len(summary),
            compression_ratio=compression_ratio,
            model_used=result.model,
            processing_time_ms=round(elapsed_ms, 2),
            request_id=request.request_id,
        )

"""
Text classification service.

Uses a structured JSON prompt to get category scores from the AI provider.
Includes robust JSON parsing with graceful fallback on malformed output.
"""

import json
import time
import re

from src.models.schemas import (
    CategoryScore,
    ClassificationCategory,
    ClassifyRequest,
    ClassifyResponse,
)
from src.services.ai_provider import BaseAIProvider
from src.utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_CATEGORIES = [c.value for c in ClassificationCategory if c != ClassificationCategory.UNKNOWN]

_SYSTEM_PROMPT = """You are a precise text classification engine.
Your output must be valid JSON and nothing else — no markdown, no explanation.

Output schema:
{
  "primary_category": "<category name>",
  "confidence": <float 0.0-1.0>,
  "scores": { "<category>": <float>, ... },
  "reasoning": "<one sentence explanation>"
}

Rules:
- All scores must sum to 1.0 (±0.01 tolerance).
- confidence = score of primary_category.
- reasoning must be concise (max 20 words).
"""


class ClassificationService:
    def __init__(self, provider: BaseAIProvider):
        self._provider = provider

    async def classify(self, request: ClassifyRequest) -> ClassifyResponse:
        start = time.perf_counter()
        categories = request.categories or _DEFAULT_CATEGORIES

        logger.info(
            "classify.start",
            text_length=len(request.text),
            categories=categories,
            request_id=request.request_id,
        )

        user_prompt = (
            f"Classify the following text into exactly these categories: {categories}\n\n"
            f"TEXT:\n{request.text}"
        )

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        result = await self._provider.complete(
            messages=messages,
            max_tokens=256,
            temperature=0.1,  # Near-deterministic for classification
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        parsed = self._parse_classification_response(result.text, categories)

        logger.info(
            "classify.complete",
            primary=parsed["primary_category"],
            confidence=parsed["confidence"],
            latency_ms=round(elapsed_ms, 2),
        )

        all_scores = [
            CategoryScore(category=cat, confidence=score)
            for cat, score in parsed["scores"].items()
        ]
        all_scores.sort(key=lambda s: s.confidence, reverse=True)

        return ClassifyResponse(
            primary_category=parsed["primary_category"],
            confidence=parsed["confidence"],
            all_scores=all_scores,
            reasoning=parsed["reasoning"],
            model_used=result.model,
            processing_time_ms=round(elapsed_ms, 2),
            request_id=request.request_id,
        )

    def _parse_classification_response(self, raw: str, categories: list[str]) -> dict:
        """
        Parses JSON from AI output. Falls back gracefully if the model
        returns markdown fences or slightly malformed JSON.
        """
        try:
            # Strip markdown code fences if present
            clean = re.sub(r"```(?:json)?|```", "", raw).strip()
            data = json.loads(clean)

            # Validate required keys
            required = {"primary_category", "confidence", "scores", "reasoning"}
            if not required.issubset(data.keys()):
                raise ValueError("Missing required keys in classification response.")

            return data

        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                "classify.parse_error",
                error=str(exc),
                raw_response=raw[:200],
            )
            return self._build_fallback_response(raw, categories)

    def _build_fallback_response(self, raw: str, categories: list[str]) -> dict:
        """
        Last-resort fallback: uniform scores with 'general' as primary.
        Ensures the endpoint never returns a 500 due to bad AI output.
        """
        uniform_score = round(1.0 / len(categories), 4)
        scores = {cat: uniform_score for cat in categories}
        primary = "general" if "general" in categories else categories[0]
        scores[primary] = round(1.0 - uniform_score * (len(categories) - 1), 4)

        return {
            "primary_category": primary,
            "confidence": scores[primary],
            "scores": scores,
            "reasoning": "Classification fell back to uniform distribution due to parse error.",
        }

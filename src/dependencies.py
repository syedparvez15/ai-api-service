"""
Dependency injection container.

FastAPI's Depends() system calls these functions to inject
services into route handlers. The provider is instantiated once
and shared across requests (singleton pattern via module-level cache).
"""

from functools import lru_cache

from src.services.ai_provider import BaseAIProvider, get_ai_provider
from src.services.summarization_service import SummarizationService
from src.services.generation_service import GenerationService
from src.services.classification_service import ClassificationService
from src.services.chat_service import ChatService


@lru_cache()
def _provider() -> BaseAIProvider:
    """Module-level singleton AI provider."""
    return get_ai_provider()


def get_summarization_service() -> SummarizationService:
    return SummarizationService(provider=_provider())


def get_generation_service() -> GenerationService:
    return GenerationService(provider=_provider())


def get_classification_service() -> ClassificationService:
    return ClassificationService(provider=_provider())


def get_chat_service() -> ChatService:
    return ChatService(provider=_provider())

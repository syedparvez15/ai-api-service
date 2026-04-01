"""
Controllers orchestrate service calls and map service responses
to HTTP responses. They are intentionally thin — no business logic here.
"""

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
from src.services.summarization_service import SummarizationService
from src.services.generation_service import GenerationService
from src.services.classification_service import ClassificationService
from src.services.chat_service import ChatService


class SummarizationController:
    def __init__(self, service: SummarizationService):
        self._service = service

    async def handle(self, request: SummarizeRequest) -> SummarizeResponse:
        return await self._service.summarize(request)


class GenerationController:
    def __init__(self, service: GenerationService):
        self._service = service

    async def handle(self, request: GenerateRequest) -> GenerateResponse:
        return await self._service.generate(request)


class ClassificationController:
    def __init__(self, service: ClassificationService):
        self._service = service

    async def handle(self, request: ClassifyRequest) -> ClassifyResponse:
        return await self._service.classify(request)


class ChatController:
    def __init__(self, service: ChatService):
        self._service = service

    async def handle(self, request: ChatRequest) -> ChatResponse:
        return await self._service.chat(request)

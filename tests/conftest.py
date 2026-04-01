"""
Shared pytest fixtures.
The MockAIProvider is always used in tests — no real API calls.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from src.app import create_app
from src.dependencies import get_summarization_service, get_generation_service, \
    get_classification_service, get_chat_service
from src.services.ai_provider import MockAIProvider
from src.services.summarization_service import SummarizationService
from src.services.generation_service import GenerationService
from src.services.classification_service import ClassificationService
from src.services.chat_service import ChatService


@pytest.fixture
def mock_provider():
    return MockAIProvider()


@pytest.fixture
def summarization_service(mock_provider):
    return SummarizationService(provider=mock_provider)


@pytest.fixture
def generation_service(mock_provider):
    return GenerationService(provider=mock_provider)


@pytest.fixture
def classification_service(mock_provider):
    return ClassificationService(provider=mock_provider)


@pytest.fixture
def chat_service(mock_provider):
    return ChatService(provider=mock_provider)


@pytest_asyncio.fixture
async def client(
    summarization_service,
    generation_service,
    classification_service,
    chat_service,
):
    """Async test client with all services wired to MockAIProvider."""
    app = create_app()
    app.dependency_overrides[get_summarization_service] = lambda: summarization_service
    app.dependency_overrides[get_generation_service] = lambda: generation_service
    app.dependency_overrides[get_classification_service] = lambda: classification_service
    app.dependency_overrides[get_chat_service] = lambda: chat_service

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

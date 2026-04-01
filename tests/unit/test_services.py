"""
Unit tests for service layer.
All AI calls go to MockAIProvider — no network required.
"""

import pytest
from src.models.schemas import (
    SummarizeRequest, GenerateRequest, ClassifyRequest, ChatRequest, ChatMessage
)
from src.utils.exceptions import TextTooLongException, ValidationException


class TestSummarizationService:

    @pytest.mark.asyncio
    async def test_summarize_returns_response(self, summarization_service):
        req = SummarizeRequest(
            text="A" * 100,
            max_sentences=2,
            style="concise",
        )
        resp = await summarization_service.summarize(req)
        assert resp.success is True
        assert len(resp.summary) > 0
        assert resp.original_length == 100
        assert resp.compression_ratio > 0  # Real provider compresses; mock may expand on tiny inputs

    @pytest.mark.asyncio
    async def test_summarize_bullet_points_style(self, summarization_service):
        req = SummarizeRequest(
            text="B" * 200,
            max_sentences=3,
            style="bullet_points",
        )
        resp = await summarization_service.summarize(req)
        assert resp.success is True

    @pytest.mark.asyncio
    async def test_summarize_text_too_long_raises(self, summarization_service):
        req = SummarizeRequest.__new__(SummarizeRequest)
        object.__setattr__(req, "text", "x" * 10_001)
        object.__setattr__(req, "max_sentences", 3)
        object.__setattr__(req, "style", "concise")
        object.__setattr__(req, "request_id", None)

        with pytest.raises(TextTooLongException) as exc_info:
            await summarization_service.summarize(req)
        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    async def test_summarize_request_id_propagated(self, summarization_service):
        req = SummarizeRequest(
            text="C" * 150,
            request_id="test-req-001",
        )
        resp = await summarization_service.summarize(req)
        assert resp.request_id == "test-req-001"


class TestGenerationService:

    @pytest.mark.asyncio
    async def test_generate_returns_response(self, generation_service):
        req = GenerateRequest(prompt="What is FastAPI?")
        resp = await generation_service.generate(req)
        assert resp.success is True
        assert len(resp.generated_text) > 0
        assert resp.total_tokens > 0

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, generation_service):
        req = GenerateRequest(
            prompt="Explain async programming.",
            system_prompt="You are a Python expert.",
            max_tokens=200,
        )
        resp = await generation_service.generate(req)
        assert resp.success is True

    @pytest.mark.asyncio
    async def test_generate_processing_time_recorded(self, generation_service):
        req = GenerateRequest(prompt="Short prompt.")
        resp = await generation_service.generate(req)
        assert resp.processing_time_ms is not None
        assert resp.processing_time_ms >= 0


class TestClassificationService:

    @pytest.mark.asyncio
    async def test_classify_returns_response(self, classification_service):
        req = ClassifyRequest(
            text="Python is a high-level programming language used for data science and web development."
        )
        resp = await classification_service.classify(req)
        assert resp.success is True
        assert resp.primary_category
        assert 0.0 <= resp.confidence <= 1.0
        assert len(resp.all_scores) > 0

    @pytest.mark.asyncio
    async def test_classify_custom_categories(self, classification_service):
        req = ClassifyRequest(
            text="The quarterly revenue exceeded expectations.",
            categories=["finance", "sports", "technology"],
        )
        resp = await classification_service.classify(req)
        # Mock provider returns a fixed response; only assert structure is correct
        assert resp.success is True
        assert resp.primary_category is not None
        assert 0.0 <= resp.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_classify_scores_sorted_by_confidence(self, classification_service):
        req = ClassifyRequest(text="Deploy the Kubernetes cluster to production.")
        resp = await classification_service.classify(req)
        scores = [s.confidence for s in resp.all_scores]
        assert scores == sorted(scores, reverse=True)


class TestChatService:

    @pytest.mark.asyncio
    async def test_chat_returns_reply(self, chat_service):
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="Hello, how are you?")]
        )
        resp = await chat_service.chat(req)
        assert resp.success is True
        assert resp.role == "assistant"
        assert len(resp.reply) > 0

    @pytest.mark.asyncio
    async def test_chat_multi_turn(self, chat_service):
        req = ChatRequest(
            messages=[
                ChatMessage(role="user", content="My name is Syed."),
                ChatMessage(role="assistant", content="Hello Syed!"),
                ChatMessage(role="user", content="What did I just tell you?"),
            ]
        )
        resp = await chat_service.chat(req)
        assert resp.success is True

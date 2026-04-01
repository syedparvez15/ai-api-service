"""
Unit tests for request/response schema validation.
These run purely in-process — no HTTP, no AI calls.
"""

import pytest
from pydantic import ValidationError
from src.models.schemas import (
    SummarizeRequest, GenerateRequest, ClassifyRequest, ChatRequest, ChatMessage
)


class TestSummarizeRequest:

    def test_valid_request(self):
        req = SummarizeRequest(text="A" * 100)
        assert req.style == "concise"
        assert req.max_sentences == 3

    def test_text_too_short_raises(self):
        with pytest.raises(ValidationError):
            SummarizeRequest(text="short")

    def test_text_too_long_raises(self):
        with pytest.raises(ValidationError):
            SummarizeRequest(text="x" * 10_001)

    def test_invalid_style_raises(self):
        with pytest.raises(ValidationError):
            SummarizeRequest(text="A" * 100, style="nonsense")

    def test_max_sentences_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            SummarizeRequest(text="A" * 100, max_sentences=0)
        with pytest.raises(ValidationError):
            SummarizeRequest(text="A" * 100, max_sentences=11)

    def test_all_valid_styles(self):
        for style in ("concise", "detailed", "bullet_points"):
            req = SummarizeRequest(text="A" * 100, style=style)
            assert req.style == style


class TestGenerateRequest:

    def test_valid_request(self):
        req = GenerateRequest(prompt="Explain microservices.")
        assert req.temperature == 0.7
        assert req.max_tokens == 512

    def test_prompt_too_short_raises(self):
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="Hi")

    def test_temperature_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="Valid prompt", temperature=-0.1)
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="Valid prompt", temperature=2.1)

    def test_max_tokens_limits(self):
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="Valid prompt", max_tokens=10)
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="Valid prompt", max_tokens=3000)


class TestClassifyRequest:

    def test_valid_request(self):
        req = ClassifyRequest(text="Deploy the API to production.")
        assert req.categories is None

    def test_custom_categories(self):
        req = ClassifyRequest(
            text="Deploy the API to production.",
            categories=["tech", "business"],
        )
        assert req.categories == ["tech", "business"]

    def test_single_category_raises(self):
        with pytest.raises(ValidationError):
            ClassifyRequest(
                text="Some text here.",
                categories=["only_one"],
            )

    def test_categories_are_lowercased(self):
        req = ClassifyRequest(
            text="Some text for classification.",
            categories=["TECH", "Business"],
        )
        assert req.categories == ["tech", "business"]


class TestChatRequest:

    def test_valid_request(self):
        req = ChatRequest(
            messages=[ChatMessage(role="user", content="Hello")]
        )
        assert len(req.messages) == 1

    def test_last_message_must_be_user(self):
        with pytest.raises(ValidationError):
            ChatRequest(messages=[
                ChatMessage(role="user", content="Hi"),
                ChatMessage(role="assistant", content="Hello"),
            ])

    def test_invalid_role_raises(self):
        with pytest.raises(ValidationError):
            ChatMessage(role="bot", content="Hello")

    def test_empty_messages_raises(self):
        with pytest.raises(ValidationError):
            ChatRequest(messages=[])

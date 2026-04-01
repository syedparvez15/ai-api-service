"""
Integration tests — exercising the full HTTP stack via AsyncClient.
All AI calls are mocked; no external services required.
"""

import pytest


class TestHealthEndpoints:

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "version" in data
        assert "uptime_seconds" in data

    @pytest.mark.asyncio
    async def test_root_returns_service_info(self, client):
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "service" in data
        assert "docs" in data


class TestSummarizeEndpoint:

    @pytest.mark.asyncio
    async def test_summarize_valid_request(self, client):
        resp = await client.post("/api/v1/summarize", json={
            "text": "Artificial intelligence is transforming every industry. " * 5,
            "max_sentences": 2,
            "style": "concise",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "summary" in data
        assert data["original_length"] > 0
        assert data["compression_ratio"] > 0

    @pytest.mark.asyncio
    async def test_summarize_with_request_id(self, client):
        resp = await client.post("/api/v1/summarize", json={
            "text": "Test content for summarization. " * 5,
            "request_id": "test-xyz-999",
        })
        assert resp.status_code == 200
        assert resp.json()["request_id"] == "test-xyz-999"

    @pytest.mark.asyncio
    async def test_summarize_text_too_short_returns_422(self, client):
        resp = await client.post("/api/v1/summarize", json={"text": "Too short."})
        assert resp.status_code == 422
        data = resp.json()
        assert data["success"] is False
        assert "error_code" in data

    @pytest.mark.asyncio
    async def test_summarize_invalid_style_returns_422(self, client):
        resp = await client.post("/api/v1/summarize", json={
            "text": "Valid text that is long enough for validation testing." * 3,
            "style": "invalid_style",
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_summarize_missing_text_returns_422(self, client):
        resp = await client.post("/api/v1/summarize", json={"max_sentences": 3})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_summarize_response_has_processing_time(self, client):
        resp = await client.post("/api/v1/summarize", json={
            "text": "Processing time should always be present in the response. " * 4,
        })
        assert resp.status_code == 200
        assert resp.json()["processing_time_ms"] is not None

    @pytest.mark.asyncio
    async def test_summarize_response_headers(self, client):
        resp = await client.post("/api/v1/summarize", json={
            "text": "Header check content for testing the middleware. " * 4,
        })
        assert "x-request-id" in resp.headers
        assert "x-response-time" in resp.headers


class TestGenerateEndpoint:

    @pytest.mark.asyncio
    async def test_generate_valid_request(self, client):
        resp = await client.post("/api/v1/generate", json={
            "prompt": "Explain the concept of REST APIs.",
            "max_tokens": 200,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "generated_text" in data
        assert data["total_tokens"] > 0

    @pytest.mark.asyncio
    async def test_generate_with_custom_system_prompt(self, client):
        resp = await client.post("/api/v1/generate", json={
            "prompt": "Write a short poem.",
            "system_prompt": "You are a creative writer.",
            "temperature": 1.0,
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_generate_prompt_too_short_returns_422(self, client):
        resp = await client.post("/api/v1/generate", json={"prompt": "Hi"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_generate_invalid_temperature_returns_422(self, client):
        resp = await client.post("/api/v1/generate", json={
            "prompt": "Valid prompt here.",
            "temperature": 5.0,
        })
        assert resp.status_code == 422


class TestClassifyEndpoint:

    @pytest.mark.asyncio
    async def test_classify_valid_request(self, client):
        resp = await client.post("/api/v1/classify", json={
            "text": "This Python script connects to a PostgreSQL database and runs queries."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "primary_category" in data
        assert "confidence" in data
        assert len(data["all_scores"]) > 0

    @pytest.mark.asyncio
    async def test_classify_custom_categories(self, client):
        resp = await client.post("/api/v1/classify", json={
            "text": "The match ended 3-1 in the final.",
            "categories": ["sports", "finance", "politics"],
        })
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_classify_single_category_returns_422(self, client):
        resp = await client.post("/api/v1/classify", json={
            "text": "Some text to classify.",
            "categories": ["only_one"],
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_classify_all_scores_sum_to_one(self, client):
        resp = await client.post("/api/v1/classify", json={
            "text": "Machine learning models require large training datasets." * 2
        })
        assert resp.status_code == 200
        total = sum(s["confidence"] for s in resp.json()["all_scores"])
        assert abs(total - 1.0) < 0.1  # Allow tolerance for mock


class TestChatEndpoint:

    @pytest.mark.asyncio
    async def test_chat_valid_request(self, client):
        resp = await client.post("/api/v1/chat", json={
            "messages": [{"role": "user", "content": "What is machine learning?"}]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["role"] == "assistant"
        assert len(data["reply"]) > 0

    @pytest.mark.asyncio
    async def test_chat_last_message_must_be_user(self, client):
        resp = await client.post("/api/v1/chat", json={
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]
        })
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_multi_turn_conversation(self, client):
        resp = await client.post("/api/v1/chat", json={
            "messages": [
                {"role": "user", "content": "I work with Python and FastAPI."},
                {"role": "assistant", "content": "That's great!"},
                {"role": "user", "content": "What are best practices for async code?"},
            ]
        })
        assert resp.status_code == 200

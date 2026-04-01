# ai-api-service

A production-grade backend service that exposes AI capabilities via a clean, versioned REST API. Built with Python and FastAPI, this service provides text summarization, prompt-based generation, text classification, and multi-turn chat — all behind a modular, testable architecture designed to scale.

---

## Problem Statement

Teams integrating AI capabilities into their products often face the same challenges: inconsistent prompt engineering scattered across the codebase, no structured error handling for AI provider failures, missing observability, and no clear separation between business logic and the AI layer.

This service solves those problems by providing a well-defined API boundary around AI functionality — one that can be consumed by any frontend, mobile app, or internal microservice without those consumers needing to know anything about how the AI model works.

---

## Solution Approach

- **Layered architecture** separates routing, orchestration, AI logic, and data models
- **Provider abstraction** allows swapping OpenAI for any other LLM backend with zero changes to service or route code
- **Structured error handling** ensures AI provider failures (timeouts, quota limits, content filtering) are caught, logged, and returned as clean JSON error responses — never raw tracebacks
- **Mock provider** enables full local development and CI testing without an API key
- **Pydantic v2 models** enforce strict validation on every request before it reaches the AI layer

---

## Architecture

```
HTTP Request
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                    │
│                                                         │
│  Middleware Stack                                       │
│  ├── RequestLoggingMiddleware  (structured logs + IDs)  │
│  ├── CORSMiddleware                                     │
│  └── GlobalExceptionHandlers  (error envelope)         │
│                                                         │
│  Routes  (src/routes/)                                  │
│  └── POST /api/v1/summarize                            │
│  └── POST /api/v1/generate                             │
│  └── POST /api/v1/classify                             │
│  └── POST /api/v1/chat                                 │
│  └── GET  /health                                       │
│                     │                                   │
│                     ▼  FastAPI Depends()                │
│  Controllers  (src/controllers/)                        │
│  └── Thin orchestration — no business logic             │
│                     │                                   │
│                     ▼                                   │
│  Services  (src/services/)                              │
│  ├── SummarizationService   (prompt engineering)        │
│  ├── GenerationService      (prompt safety + logging)   │
│  ├── ClassificationService  (JSON prompt + parsing)     │
│  └── ChatService            (multi-turn history)        │
│                     │                                   │
│                     ▼                                   │
│  AI Provider  (src/services/ai_provider.py)             │
│  ├── OpenAIProvider    (real — uses OPENAI_API_KEY)     │
│  └── MockAIProvider    (dev/test — no API key needed)   │
└─────────────────────────────────────────────────────────┘
```

**Request flow:**
`Route Handler → Controller → Service → AI Provider → Pydantic Response Model → JSON`

Every layer has a single responsibility. The service layer contains all prompt engineering logic. The controller layer maps service output to HTTP responses. The provider layer handles all communication with the AI backend and translates provider-specific errors into domain exceptions.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11 |
| Framework | FastAPI 0.111 |
| Data Validation | Pydantic v2 |
| AI Provider | OpenAI API (gpt-3.5-turbo / gpt-4) |
| Async Runtime | Uvicorn + AnyIO |
| Caching | Redis (via cachetools for in-process) |
| Logging | structlog (JSON in prod, colored in dev) |
| Testing | pytest + pytest-asyncio + httpx |
| Container | Docker + Docker Compose |

---

## Project Structure

```
ai-api-service/
├── main.py                          # Entrypoint (uvicorn)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pytest.ini
├── .env.example
│
├── src/
│   ├── app.py                       # App factory (create_app)
│   ├── config.py                    # Pydantic-settings config
│   ├── dependencies.py              # FastAPI DI container
│   │
│   ├── routes/
│   │   ├── ai_routes.py             # /summarize /generate /classify /chat
│   │   └── health_routes.py         # /health
│   │
│   ├── controllers/
│   │   └── ai_controller.py         # Orchestration layer
│   │
│   ├── services/
│   │   ├── ai_provider.py           # OpenAI + Mock provider abstraction
│   │   ├── summarization_service.py
│   │   ├── generation_service.py
│   │   ├── classification_service.py
│   │   └── chat_service.py
│   │
│   ├── models/
│   │   └── schemas.py               # All Pydantic request/response models
│   │
│   ├── middleware/
│   │   ├── exception_handlers.py    # Global error → JSON envelope
│   │   └── request_logger.py        # Structured HTTP request logging
│   │
│   └── utils/
│       ├── logger.py                # structlog configuration
│       └── exceptions.py            # Domain exception hierarchy
│
└── tests/
    ├── conftest.py                  # Fixtures (MockProvider, async client)
    ├── unit/
    │   ├── test_services.py         # Service layer unit tests
    │   └── test_schemas.py          # Pydantic model validation tests
    └── integration/
        └── test_api_endpoints.py    # Full HTTP stack integration tests
```

---

## API Endpoints

### `POST /api/v1/summarize`

Condenses a body of text into a shorter summary.

**Request**
```json
{
  "text": "Artificial intelligence is rapidly transforming every major industry...",
  "max_sentences": 3,
  "style": "concise",
  "request_id": "req_001"
}
```

**Response**
```json
{
  "success": true,
  "request_id": "req_001",
  "summary": "AI is reshaping industries through automation and intelligent systems. Key applications span healthcare, finance, and logistics. Adoption is accelerating as costs drop.",
  "original_length": 1240,
  "summary_length": 218,
  "compression_ratio": 0.1758,
  "model_used": "gpt-3.5-turbo",
  "processing_time_ms": 842.5
}
```

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `text` | string | required | 50–10,000 characters |
| `max_sentences` | int | 3 | 1–10 |
| `style` | string | `concise` | `concise` \| `detailed` \| `bullet_points` |

---

### `POST /api/v1/generate`

Sends a prompt to the AI model and returns the generated completion.

**Request**
```json
{
  "prompt": "Explain the CAP theorem and its practical implications for distributed systems.",
  "max_tokens": 400,
  "temperature": 0.7,
  "system_prompt": "You are a senior software architect."
}
```

**Response**
```json
{
  "success": true,
  "generated_text": "The CAP theorem states that a distributed system can only guarantee two of three properties simultaneously: Consistency, Availability, and Partition tolerance...",
  "prompt_tokens": 42,
  "completion_tokens": 198,
  "total_tokens": 240,
  "model_used": "gpt-3.5-turbo",
  "finish_reason": "stop",
  "processing_time_ms": 1203.1
}
```

---

### `POST /api/v1/classify`

Classifies input text into categories with confidence scores.

**Request**
```json
{
  "text": "The patient presented with elevated cortisol levels and fatigue. A referral to endocrinology was recommended.",
  "categories": ["medical", "legal", "technical", "business"]
}
```

**Response**
```json
{
  "success": true,
  "primary_category": "medical",
  "confidence": 0.91,
  "all_scores": [
    { "category": "medical",   "confidence": 0.91 },
    { "category": "business",  "confidence": 0.05 },
    { "category": "legal",     "confidence": 0.03 },
    { "category": "technical", "confidence": 0.01 }
  ],
  "reasoning": "Text contains clinical terminology and references a medical referral.",
  "model_used": "gpt-3.5-turbo",
  "processing_time_ms": 654.2
}
```

---

### `POST /api/v1/chat`

Accepts a conversation history and returns the next assistant reply. The caller maintains and replays message history on each request (stateless server).

**Request**
```json
{
  "messages": [
    { "role": "user",      "content": "I'm building a FastAPI service with async endpoints." },
    { "role": "assistant", "content": "That's a solid choice. What aspect do you need help with?" },
    { "role": "user",      "content": "How should I handle database connections in async code?" }
  ],
  "max_tokens": 300
}
```

**Response**
```json
{
  "success": true,
  "reply": "For async FastAPI with databases, use an async ORM like SQLAlchemy 2.0 with async sessions, or databases library for raw SQL. Create the engine once at startup using lifespan events and use connection pooling...",
  "role": "assistant",
  "prompt_tokens": 85,
  "completion_tokens": 142,
  "total_tokens": 227,
  "model_used": "gpt-3.5-turbo",
  "finish_reason": "stop",
  "processing_time_ms": 1104.7
}
```

---

### `GET /health`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "production",
  "uptime_seconds": 43821.4,
  "ai_provider_healthy": true
}
```

---

## Error Responses

All errors follow a consistent envelope format:

```json
{
  "success": false,
  "error_code": "TEXT_TOO_LONG",
  "message": "Input text exceeds maximum allowed length of 10000 characters.",
  "details": {
    "max_chars": 10000,
    "received": 12450
  },
  "request_id": "req_001"
}
```

| HTTP Status | Error Code | Cause |
|-------------|------------|-------|
| 422 | `VALIDATION_ERROR` | Missing or invalid request fields |
| 422 | `TEXT_TOO_LONG` | Input exceeds character limit |
| 401 | `UNAUTHORIZED` | Invalid or missing API key |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests |
| 502 | `AI_SERVICE_ERROR` | AI provider returned an error |
| 503 | `AI_QUOTA_EXCEEDED` | Provider quota exhausted |
| 504 | `AI_TIMEOUT` | Provider did not respond in time |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## Setup & Running

### Option 1: Local (no Docker)

```bash
# Clone and set up
git clone https://github.com/syedparvez15/ai-api-service.git
cd ai-api-service

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
# (leave as mock-key to use the built-in mock provider)

# Start the server
make run
# API available at http://localhost:8000
# Docs available at http://localhost:8000/docs
```

### Option 2: Docker Compose

```bash
cp .env.example .env
docker-compose up --build
```

---

## Running Tests

```bash
# All tests with coverage
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# HTML coverage report
make test-cov
```

Tests use `MockAIProvider` — no OpenAI API key required.

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | `mock-key` | OpenAI API key. Leave unset to use mock provider. |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | Model name (e.g. `gpt-4`) |
| `OPENAI_MAX_TOKENS` | `1024` | Global token cap |
| `OPENAI_TEMPERATURE` | `0.7` | Default sampling temperature |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string for caching |
| `CACHE_TTL_SECONDS` | `300` | Response cache TTL |
| `RATE_LIMIT_PER_MINUTE` | `60` | Per-IP request limit |
| `APP_ENV` | `development` | Set to `production` to tighten CORS etc. |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |
| `LOG_FORMAT` | `json` | `json` (prod) or `console` (dev) |

---

## Future Improvements

### Near-term
- **Redis response caching** — Cache identical prompts with TTL to reduce API costs and latency by up to 80% for repeated requests
- **API key authentication** — Per-key rate limits and usage tracking via middleware
- **Async task queue** — Offload long-running requests to Celery + Redis for polling-based async results

### Medium-term
- **Streaming responses** — Server-Sent Events (SSE) for real-time token streaming to the client
- **Document ingestion endpoint** — Accept PDF/DOCX uploads, extract text, and pass to summarization pipeline
- **Prompt versioning** — Store and A/B test prompt templates with performance tracking

### Architecture evolution
- **Microservice split** — Each service (summarize, classify, chat) becomes its own deployable unit behind an API gateway (Kong / AWS API Gateway)
- **Vector search integration** — Add Pinecone or pgvector for RAG (Retrieval-Augmented Generation) to ground responses in private knowledge bases
- **Multi-provider routing** — Route requests to different providers (OpenAI, Anthropic, Cohere) based on cost, latency, or task type

---

## License

MIT License — see [LICENSE](LICENSE) for details.

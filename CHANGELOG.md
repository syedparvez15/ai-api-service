# Changelog

All notable changes to this project will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Rate limiting middleware
- Response caching layer
- Prometheus metrics endpoint

---

## [1.2.0] - 2026-05-11

### Added
- `CHANGELOG.md` to track release history
- Expanded test coverage for classification endpoint
- Mock provider support for offline CI runs

### Fixed
- Multi-turn chat context not preserved across sessions
- Classification returning empty labels on edge cases

---

## [1.1.0] - 2026-04-15

### Added
- Multi-turn chat endpoint with session context
- `MockAIProvider` for CI/CD pipeline compatibility
- Structured logging with `structlog`
- 50 passing tests across all endpoints

### Changed
- Refactored summarization endpoint for better error handling
- Improved request validation using Pydantic v2

### Fixed
- Generation endpoint timeout on large payloads
- Missing content-type header in API responses

---

## [1.0.0] - 2026-03-15

### Added
- Initial FastAPI application structure
- Summarization endpoint (`POST /api/summarize`)
- Text generation endpoint (`POST /api/generate`)
- Classification endpoint (`POST /api/classify`)
- Health check endpoint (`GET /health`)
- Docker support with `Dockerfile` and `docker-compose.yml`
- Redis integration for session management
- Full test suite with pytest
- CI pipeline with GitHub Actions

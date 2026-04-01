.PHONY: install run test lint format docker-build docker-up docker-down clean

# ── Setup ────────────────────────────────────────────────────────────────────
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	cp -n .env.example .env || true

# ── Development ──────────────────────────────────────────────────────────────
run:
	uvicorn main:app --host 0.0.0.0 --port 8000 --reload

run-prod:
	uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# ── Testing ──────────────────────────────────────────────────────────────────
test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-cov:
	pytest --cov=src --cov-report=html
	@echo "Coverage report: htmlcov/index.html"

# ── Code Quality ─────────────────────────────────────────────────────────────
lint:
	flake8 src/ tests/ --max-line-length=100 --ignore=E501,W503

format:
	black src/ tests/ main.py

type-check:
	mypy src/ --ignore-missing-imports

# ── Docker ───────────────────────────────────────────────────────────────────
docker-build:
	docker build -t ai-api-service:latest .

docker-up:
	docker-compose up --build -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

# ── Utilities ────────────────────────────────────────────────────────────────
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/

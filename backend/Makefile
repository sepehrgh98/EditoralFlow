.PHONY: start stop restart rebuild logs ps dev data install hooks lint format typecheck test test-live check

# --- Docker ---
start:
	docker compose up -d backend

stop:
	docker compose stop backend

restart:
	docker compose restart backend

rebuild:
	docker compose up -d --build backend

logs:
	docker compose logs -f backend

ps:
	docker compose ps

# --- Local development (uv) ---
# Run the backend without Docker, reloading on code changes
dev:
	uv run uvicorn --factory app.main:create_app --reload --port 8000

# Download the SciFact corpus once into data/ (gitignored)
data:
	uv run python -m scripts.download_scifact

install:
	uv sync

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .

typecheck:
	uv run pyright

test:
	uv run pytest

# Calls the real model from your settings (Ollama: free). Not run by check or CI.
test-live:
	uv run pytest -m live -v

# Turn on the pre-commit checks for this clone (once)
hooks:
	cd .. && uv run --project backend pre-commit install

check: lint typecheck test

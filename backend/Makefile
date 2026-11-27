.PHONY: start stop restart rebuild logs ps dev install lint format typecheck test check

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

install:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run pyright

test:
	uv run pytest

check: lint typecheck test

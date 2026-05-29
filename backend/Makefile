.PHONY: start stop restart rebuild logs ps

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

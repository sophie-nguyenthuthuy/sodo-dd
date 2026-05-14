SHELL := /bin/bash
COMPOSE := docker compose

.PHONY: help up down logs ps build rebuild migrate revision seed test lint fmt typecheck shell psql clean

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk 'BEGIN{FS=":.*?##"};{printf "  \033[36m%-12s\033[0m %s\n",$$1,$$2}'

up: ## start full stack (api, worker, web, postgres, redis, minio)
	$(COMPOSE) up -d --build
	@echo "API:    http://localhost:8000/docs"
	@echo "Web:    http://localhost:3000"
	@echo "MinIO:  http://localhost:9001  (minio_admin / minio_admin_secret)"

down: ## stop and remove containers
	$(COMPOSE) down

logs: ## tail logs
	$(COMPOSE) logs -f --tail=100

ps:
	$(COMPOSE) ps

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) build --no-cache

migrate: ## apply alembic migrations
	$(COMPOSE) exec api alembic upgrade head

revision: ## make a new alembic revision: make revision m="add foo"
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(m)"

seed: ## seed demo org + API key
	$(COMPOSE) exec api python -m app.scripts.seed

test:
	$(COMPOSE) exec api pytest -q

lint:
	$(COMPOSE) exec api ruff check app tests
	$(COMPOSE) exec api ruff format --check app tests

fmt:
	$(COMPOSE) exec api ruff format app tests
	$(COMPOSE) exec api ruff check --fix app tests

typecheck:
	$(COMPOSE) exec api mypy app

shell:
	$(COMPOSE) exec api bash

psql:
	$(COMPOSE) exec postgres psql -U sodo -d sodo_dd

clean: ## nuke volumes (DESTROYS DATA)
	$(COMPOSE) down -v

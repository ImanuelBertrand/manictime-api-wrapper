DC := docker compose
EXEC := $(DC) exec web

.DEFAULT_GOAL := info

.PHONY: info up down build reset logs shell claude test lint fix typecheck

info:
	@echo "ManicTime API Wrapper — available targets:"
	@echo ""
	@echo "  up         Start all services"
	@echo "  down       Stop all services"
	@echo "  build      Rebuild images and start"
	@echo "  reset      Full reset (down -v + up)"
	@echo "  logs       Follow logs (all services; use s=web to filter)"
	@echo "  shell      Open a bash shell in the web container"
	@echo "  claude     Open Claude Code in the web container"
	@echo "  test       Run test suite"
	@echo "  lint       Run ruff linter (check only)"
	@echo "  fix        Run ruff and apply fixes"
	@echo "  typecheck  Run ty type checker"


up:
	$(DC) up -d

down:
	$(DC) down

build:
	$(DC) up -d --build

reset:
	$(DC) down -v
	$(DC) up -d

logs:
	$(DC) logs -f $(s)

shell:
	$(EXEC) bash

claude:
	$(EXEC) bash docker/claude.sh

test:
	$(EXEC) bash -c 'python -m pytest $(args)'

lint:
	$(EXEC) bash -c 'ruff check . && ruff format --check .'

fix:
	$(EXEC) bash -c 'ruff check --fix . && ruff format .'

typecheck:
	$(EXEC) bash -c 'ty check .'

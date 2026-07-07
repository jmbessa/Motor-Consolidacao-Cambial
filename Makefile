# Makefile — porta de entrada única do projeto.
#
# Alvos de DESENVOLVIMENTO usam o venv local (rápido, para o ciclo TDD).
# Alvos de EXECUÇÃO/ENTREGA usam Docker Compose (backend + frontend + MySQL) e
# são implementados na fatia de infraestrutura — por ora são placeholders
# explícitos, para não fingir comportamento inexistente.

VENV_PY := .venv/Scripts/python.exe

.DEFAULT_GOAL := help
.PHONY: help install test test-integration run up down logs migrate seed clean

help: ## Lista os alvos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

# --- Desenvolvimento (venv local) ---

install: ## Cria o venv e instala as dependências (modo dev)
	python -m venv .venv
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -e ".[dev]"

test: ## Roda a suíte de testes
	$(VENV_PY) -m pytest

# --- Execução / entrega (Docker Compose) ---

COMPOSE := docker compose
# Alvos rodados do host (venv) contra o container publicam o MySQL em 127.0.0.1
# (o default MOTOR_DB_HOST=db só resolve na rede interna do Compose — Fatia 8).
HOST_DB := MOTOR_DB_HOST=127.0.0.1
TEST_DB_URL := mysql+pymysql://motor:motor@127.0.0.1:3306/motor_cambial

up: ## Sobe o MySQL e espera ficar healthy
	$(COMPOSE) up -d --wait db

down: ## Derruba o container (mantém o volume de dados)
	$(COMPOSE) down

logs: ## Acompanha os logs do MySQL
	$(COMPOSE) logs -f db

migrate: ## Aplica o schema (criar_schema) no MySQL
	$(HOST_DB) $(VENV_PY) -m motor_cambial.adapters.outbound.persistence.migrate

test-integration: ## Roda os testes de integração contra o MySQL do container
	MOTOR_TEST_DB_URL=$(TEST_DB_URL) $(VENV_PY) -m pytest -m integration

run: ## Prepara a camada de dados (up + migrate). O app (CLI/API/front) chega nas Fatias 7/8
	@echo "App completo chega nas Fatias 7/8. Por ora: sobe o MySQL e aplica o schema."
	$(MAKE) up
	$(MAKE) migrate

seed: ## [Fatia 7] Carrega data/exposicoes.json (depende do loader da CLI)
	@echo "[Fatia 7] seed depende do loader de exposicoes.json (CLI), ainda indisponivel."

clean: ## Derruba o container COM o volume e limpa caches locais
	$(COMPOSE) down -v
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

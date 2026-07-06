# Makefile — porta de entrada única do projeto.
#
# Alvos de DESENVOLVIMENTO usam o venv local (rápido, para o ciclo TDD).
# Alvos de EXECUÇÃO/ENTREGA usam Docker Compose (backend + frontend + MySQL) e
# são implementados na fatia de infraestrutura — por ora são placeholders
# explícitos, para não fingir comportamento inexistente.

VENV_PY := .venv/Scripts/python.exe

.DEFAULT_GOAL := help
.PHONY: help install test run up down logs migrate seed clean

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

# --- Execução / entrega (Docker Compose) — fatia de infraestrutura ---

run: up ## Sobe todo o stack (build + containers + migrations) — atalho principal

up: ## Sobe backend + frontend + MySQL
	@echo "[TODO fatia de infra] docker compose up --build -d"

down: ## Derruba o stack
	@echo "[TODO fatia de infra] docker compose down"

logs: ## Acompanha os logs dos containers
	@echo "[TODO fatia de infra] docker compose logs -f"

migrate: ## Aplica o schema/migrations no MySQL
	@echo "[TODO fatia de infra] aplicar migrations no MySQL"

seed: ## Carrega a massa de dados de exemplo
	@echo "[TODO fatia de infra] carregar data/exposicoes.json"

clean: ## Remove artefatos locais (venv, caches)
	@echo "[TODO fatia de infra] remover volumes/containers; limpar caches"

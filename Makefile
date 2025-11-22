COMPOSE ?= docker compose
STACK_SERVICES ?= timescaledb pgvector redis mosquitto ollama prometheus grafana kpi orchestrator
UI_DIR ?= ui
REPO_ROOT ?= $(abspath ..)
PYTHON ?= $(REPO_ROOT)/.venv/bin/python3
RAG_DIR ?= services/rag
RAG_APP ?= rag.api:app
RAG_PORT ?= 8002


.PHONY: up down logs ps services services-build services-stop seed lint ui-install ui-dev ui-build rag-install rag-serve

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

services:
	$(COMPOSE) up -d $(STACK_SERVICES)

services-build:
	$(COMPOSE) up -d --build  $(STACK_SERVICES)

services-stop:
	$(COMPOSE) stop $(STACK_SERVICES)

seed:
	cd services/kpi && $(PYTHON) -m app.scripts.seed_timescale --truncate

lint:
	@echo "TODO: implement repo-wide linting"

ui-install:
	cd $(UI_DIR) && npm install

ui-dev: ui-install
	cd $(UI_DIR) && npm run dev

ui-build: ui-install
	cd $(UI_DIR) && npm run build

rag-install:
	cd $(RAG_DIR) && $(PYTHON) -m pip install -r requirements.txt

rag-serve:
	cd $(RAG_DIR) && $(PYTHON) -m uvicorn $(RAG_APP) --host 0.0.0.0 --port $(RAG_PORT)

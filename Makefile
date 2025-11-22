COMPOSE ?= docker compose


.PHONY: up down logs ps seed lint

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

seed:
	@echo "TODO: implement data seeding scripts"

lint:
	@echo "TODO: implement repo-wide linting"

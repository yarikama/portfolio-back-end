SHELL := /bin/bash

# Variables definitions
# -----------------------------------------------------------------------------

ifeq ($(TIMEOUT),)
TIMEOUT := 60
endif

ifeq ($(MODEL_PATH),)
MODEL_PATH := ./ml/model/
endif

ifeq ($(MODEL_NAME),)
MODEL_NAME := model.pkl
endif

ENV ?= local
ENV_FILE := .env.${ENV}

# Target section and Global definitions
# -----------------------------------------------------------------------------
.PHONY: all clean test install run deploy down lint format hash logs shell rebuild migrate-prod

all: clean install test

install: generate_dot_env
	uv sync --all-extras

test:
	uv run pytest -vv --show-capture=all

run:
	PYTHONPATH=app/ uv run uvicorn main:app --reload --host 0.0.0.0 --port 8080

lint:
	uv run ruff check app/

format:
	uv run ruff format app/
	uv run ruff check --fix app/

hash:
	@read -p "Enter password: " pwd && \
	hash=$$(uv run python -c "import bcrypt; print(bcrypt.hashpw(b'$$pwd', bcrypt.gensalt()).decode())") && \
	echo "" && \
	echo "Generated hash: $$hash" && \
	echo "" && \
	echo "Add this to .env file (no $$ escaping needed):" && \
	echo "ADMIN_PASSWORD_HASH=$$hash" && \
	echo "" && \
	read -p "Update .env.local automatically? (y/n): " update && \
	if [ "$$update" = "y" ]; then \
		if grep -q "^ADMIN_PASSWORD_HASH=" .env.local 2>/dev/null; then \
			sed -i.bak "s|^ADMIN_PASSWORD_HASH=.*|ADMIN_PASSWORD_HASH=$$hash|" .env.local && \
			echo "✓ Updated ADMIN_PASSWORD_HASH in .env.local"; \
		else \
			echo "ADMIN_PASSWORD_HASH=$$hash" >> .env.local && \
			echo "✓ Added ADMIN_PASSWORD_HASH to .env.local"; \
		fi; \
	fi

deploy: generate_dot_env
	@echo "Running in ${ENV} environment..."
	ENV_FILE=$(ENV_FILE) docker-compose build
	ENV_FILE=$(ENV_FILE) docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f app

shell:
	docker-compose exec app bash

rebuild:
	docker-compose build --no-cache
	docker-compose up -d

generate_dot_env:
	@if [[ ! -e .env.local ]]; then \
		cp .env.example .env.local; \
		echo "Created .env.local (Modify for Docker)"; \
	fi
	@if [[ ! -e .env.prod ]]; then \
		cp .env.example .env.prod; \
		echo "Created .env.prod (Modify for production: Neon, R2)"; \
	fi

clean:
	@find . -name '*.pyc' -exec rm -rf {} \;
	@find . -name '__pycache__' -exec rm -rf {} \;
	@find . -name 'Thumbs.db' -exec rm -rf {} \;
	@find . -name '*~' -exec rm -rf {} \;
	rm -rf .cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -rf htmlcov
	rm -rf .tox/
	rm -rf docs/_build

# Database Migrations
# -----------------------------------------------------------------------------

revision:
	docker-compose exec app alembic revision --autogenerate -m "$(msg)"

upgrade:
	docker-compose exec app alembic upgrade head

downgrade:
	docker-compose exec app alembic downgrade -1

history:
	docker-compose exec app alembic history --verbose

stamp:
	docker-compose exec app alembic stamp head

migrate-prod:
	@if [ ! -f .env.prod ]; then echo "Error: .env.prod not found!"; exit 1; fi
	@set -euo pipefail; \
	DATABASE_URL=""; \
	while IFS= read -r line || [ -n "$$line" ]; do \
		case "$$line" in \
			""|\#*) continue ;; \
			DATABASE_URL=*) DATABASE_URL="$${line#DATABASE_URL=}"; break ;; \
		esac; \
	done < .env.prod; \
	if [ -z "$$DATABASE_URL" ]; then echo "Missing DATABASE_URL in .env.prod"; exit 1; fi; \
	PYTHONPATH=app DATABASE_URL="$$DATABASE_URL" uv run alembic -c app/alembic.ini upgrade head
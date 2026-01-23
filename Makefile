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

# GCP Cloud Run configuration
GCP_PROJECT := yarikama-portfolio
GCP_REGION := us-central1
GCP_SERVICE := portfolio-backend
CLOUDSDK_PYTHON := /opt/homebrew/opt/python@3.12/bin/python3.12
GCLOUD := /opt/homebrew/share/google-cloud-sdk/bin/gcloud

ENV ?= local
ENV_FILE := .env.${ENV}

# Target section and Global definitions
# -----------------------------------------------------------------------------
.PHONY: all clean test install run deploy deploy-gcp down lint format hash logs shell rebuild

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

deploy-gcp: generate_dot_env
	@if [ ! -f .env.prod ]; then echo "Error: .env.prod not found!"; exit 1; fi
	@echo "Deploying to GCP Cloud Run using .env.prod..."
	@export $$(grep -v '^#' .env.prod | xargs) && \
	CLOUDSDK_PYTHON=$(CLOUDSDK_PYTHON) $(GCLOUD) run deploy $(GCP_SERVICE) \
		--source . \
		--platform managed \
		--region $(GCP_REGION) \
		--allow-unauthenticated \
		--port 8080 \
		--memory 512Mi \
		--cpu 1 \
		--min-instances 0 \
		--max-instances 1 \
		--project $(GCP_PROJECT) \
		--set-env-vars "DATABASE_URL=$$DATABASE_URL" \
		--set-env-vars "SECRET_KEY=$$SECRET_KEY" \
		--set-env-vars "DEBUG=False" \
		--set-env-vars "MEMOIZATION_FLAG=False" \
		--set-env-vars "ADMIN_USERNAME=$$ADMIN_USERNAME" \
		--set-env-vars "ADMIN_PASSWORD_HASH=$$ADMIN_PASSWORD_HASH" \
		--quiet
	@echo "Deployment complete!"
	@echo "Service URL: https://$(GCP_SERVICE)-790579792548.$(GCP_REGION).run.app"

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
		echo "Created .env.prod (Modify for GCP/Neon)"; \
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
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
	uv run python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('$$pwd'))"

deploy: generate_dot_env
	docker-compose build
	docker-compose up -d

deploy-gcp: generate_dot_env
	@echo "Deploying to GCP Cloud Run..."
	@export $$(grep -v '^#' .env | xargs) && \
	CLOUDSDK_PYTHON=$(CLOUDSDK_PYTHON) gcloud run deploy $(GCP_SERVICE) \
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
	@if [[ ! -e .env ]]; then \
		cp .env.example .env; \
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
